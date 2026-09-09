#!/usr/bin/env python3
"""Preflight and run three frozen ten-step stateful builds with bounded local workers."""

import argparse
import dataclasses
import hashlib
import json
import random
import subprocess
import time
from pathlib import Path

from gflo.artifacts import ArtifactStore
from gflo.broker import DockerBroker, SourceBundle
from gflo.controller import Controller, RunPlan, prepare_run
from gflo.gates import ProcessCase, ProcessGate
from gflo.ledger import WorkLedger
from gflo.model import LocalModel, ModelProfile
from gflo.pilot import IMAGE
from gflo.records import AcceptanceFinding, WorkAtom
from gflo.reporting import cost_report
from gflo.worker import InputSnapshot
from inventory_workload import BASE, CLI_DRIVER, CONTRACT, reference_update, state_oracle, steps

ROOT = Path(__file__).resolve().parents[1]


def make_gate(cases):
    return ProcessGate(
        cases=tuple(
            ProcessCase(
                command=command,
                stdin=json.dumps(given) + "\n",
                expected_stdout=json.dumps(expected, sort_keys=True) + "\n",
                seconds=30.0,
            )
            for command, given, expected in cases
        )
    )


def check(broker, source, gate):
    digest = broker.artifacts.publish(source.canonical().encode())
    rows = []
    for case in gate.cases:
        e = broker.execute(
            digest, case.command, stdin=case.stdin, seconds=case.seconds, purpose="validation"
        )
        passed = (
            e.outcome == "completed"
            and e.exit_code == 0
            and e.stdout == case.expected_stdout.encode()
        )
        rows.append({"passed": passed, "execution_digest": e.digest()})
        if not passed:
            break
    return {"passed": all(row["passed"] for row in rows), "cases": rows}


def review_workflows():
    rng = random.Random(20260911)
    workflows = []
    for index in range(6):
        stock = rng.randrange(5, 30)
        quantity = rng.randrange(1, stock + 1)
        create = {"op": "create", "sku": "A", "stock": stock}
        reserve = {"op": "reserve", "request_id": "repeat", "sku": "A", "quantity": quantity}
        ops = [
            create,
            reserve,
            reserve,
            {"op": "reserve", "request_id": "repeat", "sku": "A", "quantity": quantity + 1},
            {"op": "cancel", "request_id": "repeat"},
            {"op": "cancel", "request_id": "repeat"},
            reserve,
            {"op": "create", "sku": "B", "stock": index},
            {"op": "reserve", "request_id": "other", "sku": "B", "quantity": index + 1},
            {"op": "reserve", "request_id": "negative", "sku": "A", "quantity": -1},
            {"op": "create", "sku": "bad", "stock": True},
            {"op": "unknown"},
            {"op": "report"},
            {"op": "audit"},
        ]
        workflows.append((("python", "-c", CLI_DRIVER), ops, state_oracle(ops)))
    return workflows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--slice-result", type=Path)
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument(
        "--profile",
        choices=("vllm-python-worker-escalating-low-v1", "vllm-python-worker-escalating-tools-v1"),
        default="vllm-python-worker-escalating-low-v1",
    )
    args = parser.parse_args()
    turn_limit = 3 if args.profile == "vllm-python-worker-escalating-tools-v1" else 1
    if not args.preflight_only and (
        args.slice_result is None
        or json.loads(args.slice_result.read_text()).get("passed") is not True
    ):
        raise RuntimeError("A qualified three-module slice is required")
    args.output.mkdir(parents=True, exist_ok=args.resume)
    deployment = (ROOT / "infra/serving/vllm-5090-graphs.example.json").read_text()
    config = json.loads(deployment)
    identity = json.loads(
        subprocess.check_output(
            ["docker", "inspect", config["managed"]["name"]], text=True, timeout=15
        )
    )[0]
    image = json.loads(
        subprocess.check_output(
            ["docker", "image", "inspect", config["managed"]["image"]], text=True, timeout=15
        )
    )[0]
    if not identity["State"]["Running"] or identity["Image"] != image["Id"]:
        raise RuntimeError("Deployment mismatch")
    for flag in ["--revision", "--tokenizer-revision"]:
        cmd = identity["Config"]["Cmd"]
        if cmd[cmd.index(flag) + 1] != config["managed"]["revision"]:
            raise RuntimeError("Revision mismatch")
    specs = steps()
    review = make_gate(review_workflows())
    paths = sorted((ROOT / "gflo").glob("*.py")) + [
        Path(__file__).resolve(),
        Path(__file__).with_name("inventory_workload.py"),
    ]
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    manifest = {
        "scope": "Three ten-step stateful prepared builds; trusted harness advances source bases, not autonomous product planning",
        "policy": {
            "builds": 3,
            "atoms_per_build": 10,
            "attempts_per_atom": 2,
            "model_turns_per_attempt": turn_limit,
            "maximum_model_turns": 60 * turn_limit,
            "profile": args.profile,
            "context": 8192,
            "first_output": 2048,
            "retry_output": 4096,
            "required_complete_builds": 3,
            "maximum_false_acceptances": 0,
            "stop_on_first_failed_build": True,
        },
        "base": BASE,
        "contract": CONTRACT,
        "steps": specs,
        "review_gate": review.model_dump(mode="json"),
        "source_sha256": hashes,
        "runtime": {"image_id": image["Id"], "command": identity["Config"]["Cmd"]},
        "slice_result_sha256": hashlib.sha256(args.slice_result.read_bytes()).hexdigest()
        if args.slice_result
        else None,
    }
    path = args.output / "manifest.json"
    if args.resume:
        if json.loads(path.read_text()) != json.loads(json.dumps(manifest)):
            raise RuntimeError("Frozen workload drift")
    else:
        path.write_text(json.dumps(manifest, indent=2) + "\n")
        for name in hashes:
            p = args.output / "runtime-source" / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes((ROOT / name).read_bytes())
    preflight_path = args.output / "preflight.json"
    if not preflight_path.exists():
        broker = DockerBroker(ArtifactStore(args.output / "preflight-artifacts"), IMAGE)
        broker.qualify()
        source = SourceBundle(files=BASE)
        observations = []
        for name, writable, selected, objective, cases in specs:
            gate = make_gate(cases)
            good = SourceBundle(files=source.files | reference_update(name, writable))
            reference = check(broker, good, gate)
            bad = check(broker, source, gate)
            row = {"step": name, "reference": reference, "starting_fault": bad}
            observations.append(row)
            preflight_path.with_suffix(".partial.json").write_text(
                json.dumps(observations, indent=2) + "\n"
            )
            print(
                json.dumps(
                    {
                        "preflight": name,
                        "reference": reference["passed"],
                        "fault_rejected": not bad["passed"],
                    }
                ),
                flush=True,
            )
            if not reference["passed"] or bad["passed"]:
                raise RuntimeError("Stateful preflight failed: " + name)
            source = good
        final_review = check(broker, source, review)
        if not final_review["passed"]:
            raise RuntimeError("Reference supplemental review failed")
        preflight_path.write_text(
            json.dumps({"steps": observations, "review": final_review}, indent=2) + "\n"
        )
    if args.preflight_only:
        print("Stateful preflight passed; no model calls made", flush=True)
        return
    profile = ModelProfile(
        profile_id=args.profile,
        base_url=config["base_url"],
        model=config["model"],
        deployment_digest=hashlib.sha256(deployment.encode()).hexdigest(),
    )
    template = json.loads((ROOT / "examples/work-atom.json").read_text())
    template.update(
        graph_revision="stateful-inventory-v1",
        requirement_ids=["stateful-inventory-contract"],
        product_modules=["inventory"],
        max_attempts=2,
        context_budget={"total_tokens": 8192, "output_tokens": 4096},
        expected_outputs=[
            {
                "name": "candidate",
                "schema_digest": hashlib.sha256(
                    json.dumps(SourceBundle.model_json_schema(), sort_keys=True).encode()
                ).hexdigest(),
            }
        ],
    )
    results_path = args.output / "results.json"
    results = json.loads(results_path.read_text()) if results_path.exists() else []
    build_reviews = []
    failed = None
    with WorkLedger(args.output / "ledger.db", reserve_bytes=256 * 1024 * 1024) as ledger:
        broker = DockerBroker(ledger.artifacts, IMAGE)
        broker.qualify()
        for repetition in range(1, 4):
            source = SourceBundle(files=BASE)
            previous = None
            for ordinal, (name, writable, selected, objective, cases) in enumerate(specs, 1):
                if previous is not None:
                    ledger.accept(
                        ledger.active_lease(previous.atom.atom_id),
                        current_inputs_digest=previous.atom.inputs_digest,
                    )
                contract = (
                    CONTRACT
                    if ordinal < 9
                    else CONTRACT.replace("storage.connect(path)", "storage.open_database(path)")
                    + "\nThe old storage.connect export is removed.\n"
                )
                pin = ledger.artifacts.publish(contract.encode())
                atom_id = f"inventory-build-r{repetition}-{ordinal:02d}-{name}"
                revision = "accepted-base-" + source.digest()
                gate = make_gate(cases)
                data = template | dict(
                    atom_id=atom_id,
                    idempotency_key=atom_id,
                    objective=objective,
                    source_revision=revision,
                    inputs_digest=InputSnapshot(
                        source_digest=source.digest(), source_revision=revision
                    ).digest(),
                    writable_paths=writable,
                    prohibited_paths=[],
                    upstream_contracts=[pin],
                    required_gates=[{"gate_id": "behavior", "validator_digest": gate.digest()}],
                )
                plan = RunPlan(
                    atom=WorkAtom.model_validate_json(json.dumps(data)),
                    source=source,
                    gates={"behavior": gate},
                    model_profile=profile,
                    deployment=deployment,
                    broker_image=IMAGE,
                    max_model_turns=turn_limit,
                    selected_paths=tuple(selected),
                )
                prepare_run(ledger, plan)
                start = time.monotonic()
                state = Controller(ledger, LocalModel(ledger.artifacts, profile), broker).run(
                    atom_id
                )
                prior = next((r for r in results if r["atom_id"] == atom_id), None)
                row = {
                    "atom_id": atom_id,
                    "repetition": repetition,
                    "step": name,
                    "state": state,
                    "cost": cost_report(ledger, atom_id),
                    "elapsed_seconds": (prior["elapsed_seconds"] if prior else 0)
                    + time.monotonic()
                    - start,
                    "base_digest": source.digest(),
                    "prior_atom_id": None if previous is None else previous.atom.atom_id,
                }
                results = [r for r in results if r["atom_id"] != atom_id] + [row]
                results_path.write_text(json.dumps(results, indent=2) + "\n")
                print(
                    json.dumps(
                        {
                            "atom": atom_id,
                            "status": state["status"],
                            "attempts": len(state["attempts"]),
                        }
                    ),
                    flush=True,
                )
                if state["status"] not in ("accepted", "quarantined"):
                    raise RuntimeError("Infrastructure halt; resume explicitly")
                if state["status"] != "accepted":
                    failed = atom_id
                    break
                source = SourceBundle.model_validate_json(
                    ledger.artifacts.read(state["candidate_digest"])
                )
                previous = plan
            if failed:
                break
            review_result = check(broker, source, review)
            build_reviews.append(
                {"build": repetition, "candidate_digest": source.digest(), "review": review_result}
            )
            (args.output / "build-reviews.json").write_text(
                json.dumps(build_reviews, indent=2) + "\n"
            )
            if not review_result["passed"]:
                evidence = ledger.artifacts.publish(
                    json.dumps(review_result, sort_keys=True).encode()
                )
                ledger.record_finding(
                    AcceptanceFinding(
                        atom_id=previous.atom.atom_id,
                        contract_digest=previous.atom.digest(),
                        candidate_digest=source.digest(),
                        evidence_digest=evidence,
                        reason="Frozen whole-build supplemental workflow contradicted acceptance",
                    )
                )
                failed = previous.atom.atom_id
                break
        audit = dataclasses.asdict(ledger.audit_artifacts())
    drift = any(
        hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest
        for name, digest in hashes.items()
    )
    summary = {
        "qualified": len(build_reviews) == 3
        and not failed
        and not drift
        and not audit["missing"]
        and not audit["corrupt"],
        "completed_builds": sum(x["review"]["passed"] for x in build_reviews),
        "completed_atoms": len(results),
        "failed_atom": failed,
        "build_reviews": build_reviews,
        "source_drift": drift,
        "audit": audit,
        "attempts": sum(len(r["state"]["attempts"]) for r in results),
    }
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(
        json.dumps({k: v for k, v in summary.items() if k not in ("audit", "build_reviews")}),
        flush=True,
    )


if __name__ == "__main__":
    main()
