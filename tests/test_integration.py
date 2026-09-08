"""Prepared integration preserves input identity and independently gates combined output."""

import base64
import hashlib
import json
from pathlib import Path

import pytest

from gflo.broker import Execution, SourceBundle
from gflo.controller import RunPlan, prepare_run
from gflo.gates import ProcessCase, ProcessGate
from gflo.integration import (
    AcceptedInput,
    IntegrationInputs,
    IntegrationPlan,
    IntegrationState,
    integrate,
)
from gflo.ledger import Conflict, WorkLedger
from gflo.model import ModelProfile
from gflo.records import GateEvidence, WorkAtom
from gflo.worker import InputSnapshot

IMAGE = "sha256:" + "a" * 64


def make_fixture(ledger, *, overlap=False):
    base = SourceBundle(files={"provider.py": "def value(): return 0\n", "main.py": "pass\n"})
    pin = ledger.artifacts.publish(b"provider value() -> int; v1")
    gate = ProcessGate(cases=(ProcessCase(command=("python", "main.py"), expected_stdout="42\n"),))
    fields = json.loads(Path("examples/work-atom.json").read_text())
    fields.update(
        prohibited_paths=[],
        required_gates=[{"gate_id": "behavior", "validator_digest": gate.digest()}],
        inputs_digest=InputSnapshot(
            source_digest=base.digest(), source_revision=fields["source_revision"]
        ).digest(),
    )
    contributions = []
    for name, edits in [
        ("provider", {"provider.py": "def value(): return 42\n"}),
        (
            "consumer",
            {"provider.py": "def value(): return 99\n"}
            if overlap
            else {"main.py": "from provider import value\nprint(value())\n"},
        ),
    ]:
        child = WorkAtom.model_validate_json(
            json.dumps(
                fields
                | {
                    "atom_id": name,
                    "idempotency_key": name,
                    "writable_paths": list(edits),
                    "upstream_contracts": [pin],
                }
            )
        )
        plan = RunPlan(
            atom=child,
            source=base,
            gates={"behavior": gate},
            broker_image=IMAGE,
            deployment="fixture",
            model_profile=ModelProfile(
                base_url="http://127.0.0.1:30000/v1",
                model="fixture",
                deployment_digest=hashlib.sha256(b"fixture").hexdigest(),
            ),
        )
        prepare_run(ledger, plan)
        lease = ledger.claim(name, "fixture")
        ledger.start(lease)
        digest = ledger.artifacts.publish(
            SourceBundle(files=base.files | edits).canonical().encode()
        )
        ledger.candidate(lease, digest)
        proof = ledger.artifacts.publish(b"synthetic preaccepted fixture evidence")
        ledger.record_gate(
            lease,
            GateEvidence(
                attempt_id=lease.attempt_id,
                contract_digest=child.digest(),
                inputs_digest=child.inputs_digest,
                candidate_digest=digest,
                gate_id="behavior",
                validator_digest=gate.digest(),
                outcome="pass",
                evidence_digest=proof,
                runner_id="fixture",
            ),
        )
        ledger.accept(lease, current_inputs_digest=child.inputs_digest)
        contributions.append(
            AcceptedInput(atom_id=name, contract_digest=child.digest(), candidate_digest=digest)
        )
    inputs = IntegrationInputs(
        state=IntegrationState(base_digest=base.digest(), contracts={"provider": pin}),
        contributions=tuple(contributions),
    )
    atom = WorkAtom.model_validate_json(
        json.dumps(
            fields
            | {
                "atom_id": "integration",
                "idempotency_key": "integration",
                "writable_paths": ["provider.py", "main.py"],
                "inputs_digest": inputs.digest(),
                "upstream_contracts": [pin],
                "dependency_artifacts": [base.digest(), inputs.digest(), pin]
                + [c.candidate_digest for c in contributions],
            }
        )
    )
    return IntegrationPlan(
        atom=atom, base=base, inputs=inputs, gates={"behavior": gate}, broker_image=IMAGE
    )


class Broker:
    def __init__(self, ledger):
        self.artifacts = ledger.artifacts
        self.image = self.image_id = IMAGE
        self.qualification_digest = None
        self.calls = 0
        self.output = b"42\n"
        self.after = None

    def reconcile(self):
        pass

    def qualify(self):
        self.qualification_digest = self.artifacts.publish(b"qualified double")

    def execute(self, digest, command, stdin, seconds, purpose):
        self.calls += 1
        if self.after:
            self.after()
        return Execution(
            candidate_digest=digest,
            image_id=IMAGE,
            container_id=str(self.calls),
            command=command,
            stdin=stdin,
            purpose=purpose,
            outcome="completed",
            exit_code=0,
            oom_killed=False,
            stdout_base64=base64.b64encode(self.output).decode(),
            stderr_base64="",
            elapsed_seconds=0.1,
        )


def test_combined_output_is_gated_and_resume_is_idempotent(tmp_path):
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        plan = make_fixture(ledger)
        broker = Broker(ledger)
        result = integrate(ledger, plan, broker, lambda: plan.inputs.state)
        assert result["status"] == "accepted" and broker.calls == 1
        source = SourceBundle.model_validate_json(ledger.artifacts.read(result["candidate_digest"]))
        assert source.files == {
            "provider.py": "def value(): return 42\n",
            "main.py": "from provider import value\nprint(value())\n",
        }
        assert (
            integrate(ledger, plan, broker, lambda: plan.inputs.state) == result
            and broker.calls == 1
        )
        assert (
            ledger._db.execute(
                "SELECT count(*) FROM acceptances WHERE atom_id='integration'"
            ).fetchone()[0]
            == 1
        )


@pytest.mark.parametrize("change", ["base", "contract", "mid-gate-contract"])
def test_changed_current_inputs_prevent_integration_acceptance(tmp_path, change):
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        plan = make_fixture(ledger)
        broker = Broker(ledger)
        current = [plan.inputs.state]
        changed = IntegrationState(
            base_digest="b" * 64 if change == "base" else plan.base.digest(),
            contracts=plan.inputs.state.contracts if change == "base" else {"provider": "c" * 64},
        )
        if change == "mid-gate-contract":
            broker.after = lambda: current.__setitem__(0, changed)
        else:
            current[0] = changed
        with pytest.raises(Conflict, match="changed"):
            integrate(ledger, plan, broker, lambda: current[0])
        assert (
            ledger._db.execute(
                "SELECT count(*) FROM acceptances WHERE atom_id='integration'"
            ).fetchone()[0]
            == 0
        )
        current[0] = plan.inputs.state
        broker.after = None
        assert integrate(ledger, plan, broker, lambda: current[0])["status"] == "accepted"


def test_overlapping_contributions_require_explicit_repair(tmp_path):
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        plan = make_fixture(ledger, overlap=True)
        broker = Broker(ledger)
        with pytest.raises(Conflict, match="overlapping"):
            integrate(ledger, plan, broker, lambda: plan.inputs.state)
        assert broker.calls == 0
        with pytest.raises(KeyError):
            ledger.status("integration")


def test_stale_consumer_contract_rejected_even_when_current_pins_match_plan(tmp_path):
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        plan = make_fixture(ledger)
        new = ledger.artifacts.publish(b"provider v2 incompatible")
        fields = plan.model_dump(mode="json")
        fields["inputs"]["state"]["contracts"] = {"provider": new}
        inputs = IntegrationInputs.model_validate_json(json.dumps(fields["inputs"]))
        fields["atom"]["inputs_digest"] = inputs.digest()
        fields["atom"]["upstream_contracts"] = [new]
        fields["atom"]["dependency_artifacts"] += [inputs.digest(), new]
        plan = IntegrationPlan.model_validate_json(json.dumps(fields))
        broker = Broker(ledger)
        with pytest.raises(Conflict, match="dependency contract"):
            integrate(ledger, plan, broker, lambda: plan.inputs.state)
        assert broker.calls == 0


def test_individual_acceptance_cannot_replace_integrated_gate(tmp_path):
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        plan = make_fixture(ledger)
        broker = Broker(ledger)
        broker.output = b"wrong\n"
        result = integrate(ledger, plan, broker, lambda: plan.inputs.state)
        assert result["status"] == "retry-ready"
        assert (
            ledger._db.execute(
                "SELECT count(*) FROM acceptances WHERE atom_id='integration'"
            ).fetchone()[0]
            == 0
        )


def test_corrupt_contract_is_audited_and_blocks_accepted_reuse(tmp_path):
    from gflo.artifacts import ArtifactError

    with WorkLedger(tmp_path / "ledger.db") as ledger:
        plan = make_fixture(ledger)
        pin = plan.atom.upstream_contracts[0]
        path = ledger.artifacts.root / pin
        path.chmod(0o600)
        path.write_bytes(b"corrupted contract")
        assert pin in ledger.audit_artifacts().corrupt
        with pytest.raises(ArtifactError):
            integrate(ledger, plan, Broker(ledger), lambda: plan.inputs.state)
        assert ledger.status("provider")["status"] == "accepted"
        with pytest.raises(KeyError):
            ledger.status("integration")


def test_gate_interruption_resumes_retained_candidate(tmp_path):
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        plan = make_fixture(ledger)
        broker = Broker(ledger)

        def interrupt():
            raise KeyboardInterrupt()

        broker.after = interrupt
        with pytest.raises(KeyboardInterrupt):
            integrate(ledger, plan, broker, lambda: plan.inputs.state)
        before = ledger.status("integration")
        assert before["status"] == "validating"
        broker.after = None
        after = integrate(ledger, plan, broker, lambda: plan.inputs.state)
        assert after["status"] == "accepted"
        assert after["candidate_digest"] == before["candidate_digest"]
        assert len(after["attempts"]) == 1


def test_integration_history_shows_combined_edits(tmp_path):
    from gflo.history import change_history

    with WorkLedger(tmp_path / "ledger.db") as ledger:
        plan = make_fixture(ledger)
        integrate(ledger, plan, Broker(ledger), lambda: plan.inputs.state)
        history = change_history(ledger, "integration")
        assert history["model_profile"] is None
        assert {c["path"] for c in history["attempts"][0]["candidates"][0]["changes"]} == {
            "provider.py",
            "main.py",
        }
