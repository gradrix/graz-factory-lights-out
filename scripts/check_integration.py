#!/usr/bin/env python3
"""Qualify prepared integration with real local-model proposals and Docker gates."""

import argparse
import dataclasses
import hashlib
import json
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
from gflo.records import WorkAtom
from gflo.reporting import cost_report
from gflo.worker import InputSnapshot

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    deployment = (ROOT / "infra/serving/vllm-5090-graphs.example.json").read_text()
    config = json.loads(deployment)
    profile = ModelProfile(
        base_url=config["base_url"],
        model=config["model"],
        deployment_digest=hashlib.sha256(deployment.encode()).hexdigest(),
    )
    base = SourceBundle(
        files={
            "provider.py": "def value(): return 0\n",
            "main.py": "pass\n",
            "nested/report.py": "pass\n",
        }
    )
    contract = (
        b"provider.py exports value() -> int. Consumers must call this"
        b" function, not copy or hard-code its current result."
    )
    pin = hashlib.sha256(contract).hexdigest()
    template = json.loads((ROOT / "examples/work-atom.json").read_text())
    specs = [
        (
            "provider",
            "provider.py",
            "Implement value() in provider.py to return integer 42.",
            ("python", "-c", "from provider import value; print(value())"),
            "42\n",
        ),
        (
            "consumer",
            "main.py",
            (
                "Implement main.py: import provider.value and print its retur"
                "n value. Do not hard-code the output."
            ),
            ("python", "main.py"),
            "0\n",
        ),
        (
            "nested-consumer",
            "nested/report.py",
            (
                "Implement nested/report.py: import provider.value and print "
                "twice its return value. This file is run with runpy.run_path"
                " from the project root. Do not hard-code the output."
            ),
            ("python", "-c", "import runpy; runpy.run_path('nested/report.py')"),
            "0\n",
        ),
    ]
    plans = []
    for name, path, objective, command, expected in specs:
        gate = ProcessGate(cases=(ProcessCase(command=command, expected_stdout=expected),))
        fields = template | dict(
            atom_id=name,
            idempotency_key=name,
            objective=objective,
            writable_paths=[path],
            prohibited_paths=[],
            upstream_contracts=[pin],
            source_revision="prepared-integration-live-v1",
            required_gates=[dict(gate_id="behavior", validator_digest=gate.digest())],
        )
        fields["inputs_digest"] = InputSnapshot(
            source_digest=base.digest(), source_revision=fields["source_revision"]
        ).digest()
        plans.append(
            RunPlan(
                atom=WorkAtom.model_validate_json(json.dumps(fields)),
                source=base,
                gates={"behavior": gate},
                deployment=deployment,
                model_profile=profile,
                broker_image=IMAGE,
            )
        )
    gates = {
        name: ProcessGate(cases=(ProcessCase(command=command, expected_stdout=expected),))
        for name, command, expected in [
            ("main", specs[1][3], "42\n"),
            ("nested", specs[2][3], "84\n"),
        ]
    }
    manifest = dict(
        workload="prepared-integration-live-v1",
        plans=[p.model_dump(mode="json") for p in plans],
        integration_gates={k: v.model_dump(mode="json") for k, v in gates.items()},
        source_sha256={
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [*sorted((ROOT / "gflo").glob("*.py")), Path(__file__).resolve()]
        },
    )
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    with WorkLedger(args.output / "ledger.db", reserve_bytes=268435456) as ledger:
        ledger.artifacts.publish(contract)
        broker = DockerBroker(ledger.artifacts, IMAGE)
        controller = Controller(ledger, LocalModel(ledger.artifacts, profile), broker)
        contributions = []
        for plan in plans:
            prepare_run(ledger, plan)
            state = controller.run(plan.atom.atom_id)
            (args.output / (plan.atom.atom_id + ".json")).write_text(
                json.dumps(state, indent=2) + "\n"
            )
            print(
                json.dumps(
                    dict(
                        task=plan.atom.atom_id,
                        status=state["status"],
                        attempts=len(state["attempts"]),
                    )
                ),
                flush=True,
            )
            if state["status"] != "accepted":
                raise RuntimeError("Child did not accept; retained evidence, no fixture tuning")
            contributions.append(
                AcceptedInput(
                    atom_id=plan.atom.atom_id,
                    contract_digest=plan.atom.digest(),
                    candidate_digest=state["candidate_digest"],
                )
            )
        inputs = IntegrationInputs(
            state=IntegrationState(base_digest=base.digest(), contracts={"provider": pin}),
            contributions=tuple(contributions),
        )
        fields = template | dict(
            atom_id="integration",
            idempotency_key="integration",
            objective="Combine the three pinned accepted edits and validate both consumers.",
            writable_paths=list(base.files),
            prohibited_paths=[],
            inputs_digest=inputs.digest(),
            upstream_contracts=[pin],
            dependency_artifacts=[base.digest(), inputs.digest(), pin]
            + [c.candidate_digest for c in contributions],
            required_gates=[dict(gate_id=k, validator_digest=v.digest()) for k, v in gates.items()],
        )
        plan = IntegrationPlan(
            atom=WorkAtom.model_validate_json(json.dumps(fields)),
            base=base,
            inputs=inputs,
            gates=gates,
            broker_image=IMAGE,
        )
        (args.output / "integration-plan.json").write_text(plan.canonical() + "\n")
        (args.output / "current-state.json").write_text(inputs.state.canonical() + "\n")
        probes = []
        for changed in [
            IntegrationState(base_digest="0" * 64, contracts={"provider": pin}),
            IntegrationState(base_digest=base.digest(), contracts={"provider": "0" * 64}),
        ]:
            try:
                integrate(ledger, plan, broker, lambda: changed)
            except Conflict as exc:
                probes.append(str(exc))
            else:
                raise AssertionError("Stale integration admitted")
        result = integrate(ledger, plan, broker, lambda: inputs.state)
        assert result["status"] == "accepted"
        assert integrate(ledger, plan, broker, lambda: inputs.state) == result
        audit = dataclasses.asdict(ledger.audit_artifacts())
        assert not audit["missing"] and not audit["corrupt"]
        report = dict(
            status="passed",
            stale_probes=probes,
            integration=result,
            audit=audit,
            costs={p.atom.atom_id: cost_report(ledger, p.atom.atom_id) for p in plans},
        )
        (args.output / "result.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(dict(status="passed", evidence=str(args.output))), flush=True)


if __name__ == "__main__":
    main()
