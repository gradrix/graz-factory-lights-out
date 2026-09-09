#!/usr/bin/env python3
"""Build and qualify a prepared provider/CLI/report inventory slice using the local model."""

import argparse
import dataclasses
import hashlib
import json
import shutil
import sqlite3
import subprocess
from pathlib import Path

from gflo.broker import DockerBroker, SourceBundle
from gflo.controller import Controller, RunPlan, prepare_run
from gflo.gates import ProcessCase, ProcessGate
from gflo.integration import (
    AcceptedInput,
    IntegrationInputs,
    IntegrationPlan,
    IntegrationState,
    integrate,
)
from gflo.ledger import Conflict, WorkLedger
from gflo.model import LocalModel, ModelProfile
from gflo.pilot import IMAGE
from gflo.records import AcceptanceFinding, WorkAtom
from gflo.reporting import cost_report
from gflo.worker import InputSnapshot

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = (
    "Inventory provider v2 exports availability(*, stock, reservations) -> "
    "{available:int,reserved:int}. Stock and each reservation must be nonnegative "
    "integers (booleans are invalid), reservations must be a list, and their sum "
    "must not exceed stock. Invalid inputs raise ValueError. Available is stock "
    "minus the reservation sum; reserved is that sum. Consumers must call the "
    "provider and use its returned fields, not duplicate inventory arithmetic. "
    "This replaces the v1 positional API returning an integer."
)
BASE = {
    "provider.py": 'def availability(*, stock, reservations):\n    return {"available":stock,"reserved":0}\n',
    "main.py": 'import json,sys\nfrom provider import availability\nx=json.load(sys.stdin)\nprint(json.dumps({"available":availability(x["stock"],x["reservations"])}))\n',
    "report.py": 'import json,sys\nfrom provider import availability\nx=json.load(sys.stdin)\nprint(json.dumps({"available_total":sum(availability(r["stock"],r["reservations"]) for r in x)}))\n',
}
REFERENCE = {
    "provider.py": """def availability(*, stock, reservations):
    if type(stock) is not int or stock < 0 or type(reservations) is not list:
        raise ValueError('invalid inventory')
    if any(type(v) is not int or v < 0 for v in reservations):
        raise ValueError('invalid inventory')
    used=sum(reservations)
    if used > stock:
        raise ValueError('invalid inventory')
    return {'available':stock-used,'reserved':used}
""",
    "main.py": """import json,sys
from provider import availability
x=json.load(sys.stdin)
try:
    result=availability(stock=x['stock'],reservations=x['reservations'])
except ValueError:
    result={'error':'invalid inventory'}
print(json.dumps(result,sort_keys=True))
""",
    "report.py": """import json,sys
from provider import availability
x=json.load(sys.stdin)
try:
    rows=[availability(stock=r['stock'],reservations=r['reservations']) for r in x]
    result={'available_total':sum(r['available'] for r in rows),'reserved_total':sum(r['reserved'] for r in rows)}
except ValueError:
    result={'error':'invalid inventory'}
print(json.dumps(result,sort_keys=True))
""",
}
PROVIDER_COMMAND = (
    "python",
    "-c",
    "import json,sys,provider\nx=json.load(sys.stdin)\ntry:\n r=provider.availability(stock=x['stock'],reservations=x['reservations'])\nexcept ValueError:\n r={'error':'invalid inventory'}\nprint(json.dumps(r,sort_keys=True))",
)
PATCH = "import provider,runpy\ncalls=[]\ndef stub(*,stock,reservations):\n calls.append(stock)\n if stock<0: raise ValueError('sentinel error')\n return {'available':stock+101,'reserved':len(reservations)+9}\nprovider.availability=stub\n"


def oracle(x):
    stock, values = x["stock"], x["reservations"]
    if (
        type(stock) is not int
        or stock < 0
        or type(values) is not list
        or any(type(v) is not int or v < 0 for v in values)
        or sum(values) > stock
    ):
        return {"error": "invalid inventory"}
    return {"available": stock - sum(values), "reserved": sum(values)}


def gate(command, examples):
    return ProcessGate(
        cases=tuple(
            ProcessCase(
                command=command,
                stdin=json.dumps(x) + "\n",
                expected_stdout=json.dumps(y, sort_keys=True) + "\n",
            )
            for x, y in examples
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--qualification-summary", type=Path)
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    if not args.preflight_only and (
        args.qualification_summary is None
        or json.loads(args.qualification_summary.read_text()).get("qualified") is not True
    ):
        raise RuntimeError("Multi-class escalation qualification must pass before this trial")
    args.output.mkdir(parents=True, exist_ok=False)
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
    base = SourceBundle(files=BASE)
    pin = hashlib.sha256(CONTRACT.encode()).hexdigest()
    profile = ModelProfile(
        profile_id="vllm-python-worker-escalating-low-v1",
        base_url=config["base_url"],
        model=config["model"],
        deployment_digest=hashlib.sha256(deployment.encode()).hexdigest(),
    )
    inputs = [
        {"stock": 10, "reservations": [2, 3]},
        {"stock": 0, "reservations": []},
        {"stock": 3, "reservations": [3]},
        {"stock": 2, "reservations": [3]},
        {"stock": True, "reservations": []},
        {"stock": 4, "reservations": [False]},
        {"stock": -1, "reservations": []},
        {"stock": 2, "reservations": [-1]},
        {"stock": 10**22, "reservations": [10**21]},
    ]
    main_command = (
        "python",
        "-c",
        PATCH + "runpy.run_path('main.py',run_name='__main__'); assert len(calls)==1",
    )
    report_command = (
        "python",
        "-c",
        PATCH + "runpy.run_path('report.py',run_name='__main__'); assert calls",
    )
    child_gates = {
        "provider": gate(PROVIDER_COMMAND, [(x, oracle(x)) for x in inputs]),
        "main": gate(
            main_command,
            [
                ({"stock": 5, "reservations": [2, 1]}, {"available": 106, "reserved": 11}),
                ({"stock": -1, "reservations": []}, {"error": "invalid inventory"}),
                ({"stock": 0, "reservations": []}, {"available": 101, "reserved": 9}),
            ],
        ),
        "report": gate(
            report_command,
            [
                (
                    [{"stock": 5, "reservations": [2]}, {"stock": 7, "reservations": []}],
                    {"available_total": 214, "reserved_total": 19},
                ),
                ([{"stock": -1, "reservations": []}], {"error": "invalid inventory"}),
            ],
        ),
    }
    objectives = {
        "provider": "Implement provider.py according to the inventory v2 contract. Define the keyword-only availability function. Do not print or read stdin.",
        "main": 'Migrate main.py to inventory v2. Read one JSON object {stock,reservations} from stdin. Call provider.availability using keywords and print its complete returned record as JSON with sort_keys=True. On ValueError print {"error":"invalid inventory"}. Print no other output.',
        "report": 'Migrate report.py to inventory v2. Read a JSON list of {stock,reservations} objects. Call provider.availability using keywords for every item. Sum its returned available and reserved fields into {available_total,reserved_total}. Empty list gives both totals zero. If any call raises ValueError print only {"error":"invalid inventory"}. Print JSON with sort_keys=True and no other output.',
    }
    template = json.loads((ROOT / "examples/work-atom.json").read_text())
    template.update(
        graph_revision="inventory-slice-v1",
        requirement_ids=["inventory-v2-contract"],
        product_modules=["inventory"],
        expected_outputs=[
            {
                "name": "candidate",
                "schema_digest": hashlib.sha256(
                    json.dumps(SourceBundle.model_json_schema(), sort_keys=True).encode()
                ).hexdigest(),
            }
        ],
    )
    plans = []
    for name in ["provider", "main", "report"]:
        data = template | dict(
            atom_id="inventory-" + name,
            idempotency_key="inventory-" + name,
            objective=objectives[name],
            source_revision="inventory-v2-common-base",
            writable_paths=[name + ".py"],
            prohibited_paths=[],
            upstream_contracts=[pin],
            max_attempts=2,
            context_budget={"total_tokens": 8192, "output_tokens": 4096},
            inputs_digest=InputSnapshot(
                source_digest=base.digest(), source_revision="inventory-v2-common-base"
            ).digest(),
            required_gates=[
                {"gate_id": "behavior", "validator_digest": child_gates[name].digest()}
            ],
        )
        plans.append(
            RunPlan(
                atom=WorkAtom.model_validate_json(json.dumps(data)),
                source=base,
                gates={"behavior": child_gates[name]},
                model_profile=profile,
                deployment=deployment,
                broker_image=IMAGE,
                max_model_turns=1,
            )
        )
    report_inputs = [[], inputs[:3], [inputs[0], inputs[-1]], [inputs[0], inputs[3]]]

    def total(xs):
        rows = [oracle(x) for x in xs]
        if any("error" in r for r in rows):
            return {"error": "invalid inventory"}
        return {
            "available_total": sum(r["available"] for r in rows),
            "reserved_total": sum(r["reserved"] for r in rows),
        }

    combined_gates = {
        "provider": child_gates["provider"],
        "main": gate(("python", "main.py"), [(x, oracle(x)) for x in inputs]),
        "report": gate(("python", "report.py"), [(xs, total(xs)) for xs in report_inputs]),
    }
    paths = sorted((ROOT / "gflo").glob("*.py")) + [Path(__file__).resolve()]
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    (args.output / "manifest.json").write_text(
        json.dumps(
            {
                "scope": "Prepared three-module inventory API migration; no persistence or autonomous planning",
                "qualification_summary_sha256": (
                    hashlib.sha256(args.qualification_summary.read_bytes()).hexdigest()
                    if args.qualification_summary
                    else None
                ),
                "contract": CONTRACT,
                "plans": [p.model_dump(mode="json") for p in plans],
                "combined_gates": {k: v.model_dump(mode="json") for k, v in combined_gates.items()},
                "references": REFERENCE,
                "source_sha256": hashes,
            },
            indent=2,
        )
        + "\n"
    )
    dbpath = args.output / "ledger.db"
    with WorkLedger(dbpath, reserve_bytes=256 * 1024 * 1024) as ledger:
        ledger.artifacts.publish(CONTRACT.encode())
        broker = DockerBroker(ledger.artifacts, IMAGE)
        broker.qualify()
        checks = []
        for plan in plans:
            name = plan.atom.atom_id.removeprefix("inventory-")
            good = SourceBundle(files=BASE | {name + ".py": REFERENCE[name + ".py"]})
            for label, bundle in [("reference", good), ("starting-fault", base)]:
                digest = ledger.artifacts.publish(bundle.canonical().encode())
                passed = True
                for case in child_gates[name].cases:
                    e = broker.execute(
                        digest,
                        case.command,
                        stdin=case.stdin,
                        seconds=case.seconds,
                        purpose="validation",
                    )
                    passed = (
                        passed
                        and e.outcome == "completed"
                        and e.exit_code == 0
                        and e.stdout == case.expected_stdout.encode()
                    )
                    if not passed:
                        break
                checks.append({"task": name, "candidate": label, "passed": passed})
                if passed != (label == "reference"):
                    raise RuntimeError("Inventory preflight failed")
        (args.output / "preflight.json").write_text(json.dumps(checks, indent=2) + "\n")
        if args.preflight_only:
            print("Inventory preflight passed; no model calls made", flush=True)
            return
        contributions = []
        costs = {}
        for plan in plans:
            prepare_run(ledger, plan)
            state = Controller(ledger, LocalModel(ledger.artifacts, profile), broker).run(
                plan.atom.atom_id
            )
            (args.output / (plan.atom.atom_id + ".json")).write_text(
                json.dumps(state, indent=2) + "\n"
            )
            print(
                json.dumps(
                    {
                        "task": plan.atom.atom_id,
                        "status": state["status"],
                        "attempts": len(state["attempts"]),
                    }
                ),
                flush=True,
            )
            if state["status"] != "accepted":
                raise RuntimeError("Child failed; preserve frozen task and evidence")
            costs[plan.atom.atom_id] = cost_report(ledger, plan.atom.atom_id)
            contributions.append(
                AcceptedInput(
                    atom_id=plan.atom.atom_id,
                    contract_digest=plan.atom.digest(),
                    candidate_digest=state["candidate_digest"],
                )
            )
        pinned = IntegrationInputs(
            state=IntegrationState(base_digest=base.digest(), contracts={"provider": pin}),
            contributions=tuple(contributions),
        )
        fields = template | dict(
            atom_id="inventory-integration",
            idempotency_key="inventory-integration",
            objective="Combine pinned inventory v2 provider and consumers.",
            writable_paths=list(BASE),
            prohibited_paths=[],
            inputs_digest=pinned.digest(),
            upstream_contracts=[pin],
            dependency_artifacts=[base.digest(), pinned.digest(), pin]
            + [c.candidate_digest for c in contributions],
            required_gates=[
                {"gate_id": k, "validator_digest": v.digest()} for k, v in combined_gates.items()
            ],
        )
        combined = IntegrationPlan(
            atom=WorkAtom.model_validate_json(json.dumps(fields)),
            base=base,
            inputs=pinned,
            gates=combined_gates,
            broker_image=IMAGE,
        )
        (args.output / "integration-plan.json").write_text(combined.canonical() + "\n")
        stale = []
        for state in [
            IntegrationState(base_digest="0" * 64, contracts={"provider": pin}),
            IntegrationState(base_digest=base.digest(), contracts={"provider": "0" * 64}),
        ]:
            try:
                integrate(ledger, combined, broker, lambda: state)
            except Conflict as exc:
                stale.append(str(exc))
            else:
                raise RuntimeError("Stale dependency admitted")
        result = integrate(ledger, combined, broker, lambda: pinned.state)
        if result["status"] != "accepted":
            raise RuntimeError("Combined gates failed")
    with WorkLedger(dbpath) as ledger:
        replay = integrate(
            ledger, combined, DockerBroker(ledger.artifacts, IMAGE), lambda: pinned.state
        )
        if replay != result:
            raise RuntimeError("Restart changed accepted integration")
        audit = dataclasses.asdict(ledger.audit_artifacts())
        # Use a separate ledger fork for simulated contradictory evidence.
        fork = args.output / "finding-probe.db"
        with sqlite3.connect(fork) as target:
            ledger._db.backup(target)
        shutil.copytree(ledger.artifacts.root, Path(str(fork) + ".artifacts"))
    with WorkLedger(fork) as ledger:
        child = contributions[0]
        evidence = ledger.artifacts.publish(
            b"SYNTHETIC fault-injection finding in a copied ledger; not a discovered product defect"
        )
        ledger.record_finding(
            AcceptanceFinding(
                atom_id=child.atom_id,
                contract_digest=child.contract_digest,
                candidate_digest=child.candidate_digest,
                evidence_digest=evidence,
                reason="Synthetic copied-ledger integration invalidation probe",
            )
        )
        try:
            integrate(ledger, combined, DockerBroker(ledger.artifacts, IMAGE), lambda: pinned.state)
        except Conflict as exc:
            finding_probe = str(exc)
        else:
            raise RuntimeError("Challenged child reused")
    drift = any(
        hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest
        for name, digest in hashes.items()
    )
    summary = {
        "passed": not drift and not audit["missing"] and not audit["corrupt"],
        "integration": result,
        "stale_probes": stale,
        "restart_idempotent": True,
        "finding_probe_in_separate_copy": finding_probe,
        "costs": costs,
        "audit": audit,
        "source_drift": drift,
    }
    (args.output / "result.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"passed": summary["passed"]}), flush=True)


if __name__ == "__main__":
    main()
