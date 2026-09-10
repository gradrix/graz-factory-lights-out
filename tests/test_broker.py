"""Protocol and opt-in real Docker boundary tests for the trusted broker."""

import base64
import json
import os
from pathlib import Path
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from gflo.artifacts import ArtifactStore
from gflo.broker import LABEL, MAX_OUTPUT, BrokerError, DockerBroker, Execution, SourceBundle
from gflo.gates import ProcessCase, ProcessGate, run_gate
from gflo.ledger import Conflict, WorkLedger
from gflo.records import WorkAtom

IMAGE = "sha256:" + "a" * 64


@pytest.mark.parametrize(
    "files",
    [
        {},
        {"../escape": "x"},
        {"/absolute": "x"},
        {"a//b": "x"},
        {"a": "x", "a/b": "x"},
        {"a": "x" * 262144},
        {"a\\b": "x"},
    ],
)
def test_reject_unsafe_or_oversized_bundle(files):
    with pytest.raises(ValidationError):
        SourceBundle(files=files)


@pytest.fixture
def broker(tmp_path, monkeypatch):
    monkeypatch.setenv("DOCKER_HOST", "unix:///var/run/docker.sock")
    monkeypatch.delenv("DOCKER_CONTEXT", raising=False)
    return DockerBroker(ArtifactStore(tmp_path / "artifacts"), IMAGE)


def test_unqualified_execution_fails_closed(broker):
    with pytest.raises(BrokerError, match="qualification"):
        broker.execute("a" * 64, ("python",))


def test_remote_daemon_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv("DOCKER_HOST", "tcp://other:2375")
    monkeypatch.delenv("DOCKER_CONTEXT", raising=False)
    with pytest.raises(BrokerError, match="local"):
        DockerBroker(ArtifactStore(tmp_path / "a"), IMAGE)


def test_cleanup_refuses_foreign_ownership(broker):
    broker._docker = Mock(
        side_effect=["some-id", json.dumps([{"Config": {"Labels": {LABEL: "another-controller"}}}])]
    )
    with pytest.raises(BrokerError, match="unowned"):
        broker._remove("some-name")
    assert broker._docker.call_count == 2


def test_cleanup_on_create_error(broker):
    digest = broker.artifacts.publish(SourceBundle(files={"x": ""}).canonical().encode())
    broker._docker = Mock(side_effect=BrokerError("daemon error"))
    broker._remove = Mock()
    with pytest.raises(BrokerError, match="daemon error"):
        broker._execute(digest, ("python",), "", 1, "candidate")
    broker._remove.assert_called_once()


@pytest.fixture
def gate_setup(tmp_path, monkeypatch):
    monkeypatch.setenv("DOCKER_HOST", "unix:///var/run/docker.sock")
    monkeypatch.delenv("DOCKER_CONTEXT", raising=False)
    with WorkLedger(tmp_path / "ledger.db") as ledger:
        broker = DockerBroker(ledger.artifacts, IMAGE)
        broker.image_id = IMAGE
        broker.qualification_digest = ledger.artifacts.publish(b"qualified test double")
        plan = ProcessGate(
            cases=(ProcessCase(command=("python", "main.py"), expected_stdout="42\n"),)
        )
        fields = json.loads((Path(__file__).parents[1] / "examples/work-atom.json").read_text())
        fields["required_gates"] = [{"gate_id": "behavior", "validator_digest": plan.digest()}]
        atom = WorkAtom.model_validate_json(json.dumps(fields))
        ledger.submit(atom)
        lease = ledger.claim(atom.atom_id, "trusted-controller")
        ledger.start(lease)
        digest = ledger.artifacts.publish(
            SourceBundle(files={"main.py": "print(42)"}).canonical().encode()
        )
        ledger.candidate(lease, digest)
        yield ledger, broker, plan, atom, lease, digest


@pytest.mark.parametrize("failure", [None, "wrong-output", "exit", "timeout", "evaluator"])
def test_gate_distinguishes_candidate_and_evaluator_failure(gate_setup, failure):
    ledger, broker, plan, atom, lease, digest = gate_setup
    result = Execution(
        candidate_digest=digest,
        image_id=IMAGE,
        container_id="one",
        command=plan.cases[0].command,
        stdin="",
        purpose="validation",
        outcome="timeout" if failure == "timeout" else "completed",
        exit_code=1 if failure == "exit" else 0,
        oom_killed=False,
        stdout_base64=base64.b64encode(b"wrong" if failure == "wrong-output" else b"42\n").decode(),
        stderr_base64="",
        elapsed_seconds=0.1,
    )
    broker.execute = Mock(
        return_value=result, side_effect=BrokerError("daemon") if failure == "evaluator" else None
    )
    receipt = run_gate(ledger, broker, lease, "behavior", plan)
    expected = "inconclusive" if failure == "evaluator" else "fail" if failure else "pass"
    assert receipt.outcome == expected
    assert receipt.candidate_digest == digest
    assert receipt.inputs_digest == atom.inputs_digest
    evidence = json.loads(ledger.artifacts.read(receipt.evidence_digest))
    assert evidence["plan_digest"] == plan.digest()
    if failure:
        with pytest.raises(Conflict):
            ledger.accept(lease, current_inputs_digest=atom.inputs_digest)
    else:
        assert (
            ledger.accept(lease, current_inputs_digest=atom.inputs_digest).candidate_digest
            == digest
        )
    # The broker gets only actual input, never the expected output or validator plan.
    assert "expected_stdout" not in broker.execute.call_args.kwargs


def test_wrong_plan_never_executes(gate_setup):
    ledger, broker, plan, atom, lease, digest = gate_setup
    broker.execute = Mock()
    changed = ProcessGate(cases=(ProcessCase(command=("true",), expected_stdout=""),))
    with pytest.raises(Conflict):
        run_gate(ledger, broker, lease, "behavior", changed)
    broker.execute.assert_not_called()


@pytest.fixture(scope="module")
def live_broker(tmp_path_factory):
    image = os.environ.get("GFLO_BROKER_TEST_IMAGE")
    if not image:
        pytest.skip("Set GFLO_BROKER_TEST_IMAGE to an installed pinned Python image")
    root = Path(os.environ.get("GFLO_BROKER_EVIDENCE", str(tmp_path_factory.mktemp("broker-live"))))
    root.mkdir(parents=True, exist_ok=True)
    broker = DockerBroker(ArtifactStore(root / "ledger.db.artifacts"), image)
    broker.qualify()
    yield broker
    broker.reconcile()


def publish(broker, code):
    return broker.artifacts.publish(SourceBundle(files={"main.py": code}).canonical().encode())


def test_live_candidate_and_validation_are_clean_and_separate(live_broker):
    code = (
        "from pathlib import Path\np=Path('/tmp/marker')\n"
        "print(p.exists())\np.write_text('changed')\n"
    )
    digest = publish(live_broker, code)
    first = live_broker.execute(digest, ("python", "main.py"))
    second = live_broker.execute(digest, ("python", "main.py"), purpose="validation")
    assert first.stdout == second.stdout == b"False\n"
    assert first.container_id != second.container_id
    assert (
        live_broker.artifacts.read(digest)
        == SourceBundle(files={"main.py": code}).canonical().encode()
    )


def test_live_no_host_credentials_network_or_validator_access(live_broker, monkeypatch):
    monkeypatch.setenv("GFLO_SECRET_SENTINEL", "must-not-enter")
    code = """
import os, json
from pathlib import Path
print(json.dumps({
 'secret':os.getenv('GFLO_SECRET_SENTINEL'),
 'socket':Path('/var/run/docker.sock').exists(),
 'host':Path('/home/gradrix/repos/graz-factory-lights-out').exists(),
 'validators':Path('/validators').exists(),
 'interfaces':sorted(p.name for p in Path('/sys/class/net').iterdir())
},sort_keys=True))
"""
    result = live_broker.execute(publish(live_broker, code), ("python", "main.py"))
    assert json.loads(result.stdout) == {
        "secret": None,
        "socket": False,
        "host": False,
        "validators": False,
        "interfaces": ["lo"],
    }


@pytest.mark.parametrize(
    "code,seconds,expected",
    [
        ("import time;time.sleep(20)", 1, "timeout"),
        ("import os\nwhile True: os.write(1,b'x'*65536)", 10, "output-limit"),
    ],
)
def test_live_bounds_and_cleanup(live_broker, code, seconds, expected):
    result = live_broker.execute(publish(live_broker, code), ("python", "main.py"), seconds=seconds)
    assert result.outcome == expected
    assert len(result.stdout) <= MAX_OUTPUT
    assert live_broker._docker("ps", "-aq", "--filter", f"label={LABEL}={live_broker.owner}") == ""


def test_live_interruption_cleans_created_container(live_broker, monkeypatch):
    def interrupt(*args):
        raise KeyboardInterrupt()

    monkeypatch.setattr(live_broker, "_attach", interrupt)
    with pytest.raises(KeyboardInterrupt):
        live_broker.execute(publish(live_broker, "print(1)"), ("python", "main.py"))
    assert live_broker._docker("ps", "-aq", "--filter", f"label={LABEL}={live_broker.owner}") == ""


def test_missing_control_refuses_to_start(broker):
    digest = publish(broker, "print(1)")
    broker.image_id = IMAGE
    broker._docker = Mock(
        side_effect=[
            "container",
            json.dumps(
                [
                    {
                        "Image": IMAGE,
                        "Mounts": [],
                        "HostConfig": {"Privileged": True},
                    }
                ]
            ),
        ]
    )
    broker._remove = Mock()
    broker._attach = Mock()
    with pytest.raises(BrokerError, match="controls"):
        broker._execute(digest, ("python", "main.py"), "", 1, "candidate")
    broker._attach.assert_not_called()
    broker._remove.assert_called_once()


def test_live_trusted_gate_and_durable_acceptance(live_broker):
    plan = ProcessGate(
        cases=(
            ProcessCase(command=("python", "main.py"), stdin="20\n", expected_stdout="40\n"),
            ProcessCase(command=("python", "main.py"), stdin="-3\n", expected_stdout="-6\n"),
        )
    )
    fields = json.loads((Path(__file__).parents[1] / "examples/work-atom.json").read_text())
    fields["required_gates"] = [{"gate_id": "behavior", "validator_digest": plan.digest()}]
    fields["atom_id"] = fields["idempotency_key"] = "live-broker-gate"
    atom = WorkAtom.model_validate_json(json.dumps(fields))
    path = live_broker.artifacts.root.parent / "ledger.db"
    with WorkLedger(path) as ledger:
        ledger.submit(atom)
        lease = ledger.claim(atom.atom_id, "trusted-controller")
        ledger.start(lease)
        digest = publish(live_broker, "print(int(input()) * 2)")
        # Candidate smoke has its own disposable environment.
        result = live_broker.execute(digest, ("python", "main.py"), stdin="1\n")
        assert result.stdout == b"2\n"
        ledger.candidate(lease, digest)
        receipt = run_gate(ledger, live_broker, lease, "behavior", plan)
        assert receipt.outcome == "pass"
        evidence = json.loads(ledger.artifacts.read(receipt.evidence_digest))
        ids = {r["container_id"] for r in evidence["executions"]}
        assert len(ids) == 2 and result.container_id not in ids
        ledger.accept(lease, current_inputs_digest=atom.inputs_digest)
    with WorkLedger(path) as ledger:
        assert ledger.status(atom.atom_id)["status"] == "accepted"
        assert ledger.audit_artifacts().missing == ()


def test_live_reconcile_only_owned_stale_containers(live_broker):
    import uuid

    name = "gflo-attempt-stale-" + uuid.uuid4().hex
    live_broker._docker(
        "create",
        "--name",
        name,
        "--label",
        f"{LABEL}={live_broker.owner}",
        "--network",
        "none",
        "--read-only",
        live_broker.image_id,
        "true",
    )
    live_broker.reconcile()
    assert live_broker._docker("ps", "-aq", "--filter", f"name={name}") == ""


def test_live_interrupt_during_execution(live_broker, monkeypatch):
    import signal
    import threading

    original = live_broker._attach

    def interrupted_attach(*args):
        timer = threading.Timer(0.75, lambda: os.kill(os.getpid(), signal.SIGINT))
        timer.start()
        try:
            return original(*args)
        finally:
            timer.cancel()
            timer.join(timeout=1)

    monkeypatch.setattr(live_broker, "_attach", interrupted_attach)
    with pytest.raises(KeyboardInterrupt):
        live_broker.execute(
            publish(live_broker, "import time; time.sleep(30)"), ("python", "main.py"), seconds=10
        )
    assert live_broker._docker("ps", "-aq", "--filter", f"label={LABEL}={live_broker.owner}") == ""


def test_forged_lease_never_dispatches_gate(gate_setup):
    ledger, broker, plan, atom, lease, digest = gate_setup
    broker.execute = Mock()
    forged = lease.model_copy(update={"token": "forged"})
    with pytest.raises(Conflict):
        run_gate(ledger, broker, forged, "behavior", plan)
    broker.execute.assert_not_called()


@pytest.mark.parametrize(
    "change",
    [
        {"candidate_digest": "b" * 64},
        {"command": ("python", "other.py")},
        {"stdin": "wrong input"},
        {"purpose": "candidate"},
        {"image_id": "sha256:" + "b" * 64},
        {"container_id": ""},
        {"stdout_base64": "NDIK!!!"},
        {"elapsed_seconds": float("nan")},
    ],
)
def test_mismatched_execution_report_never_passes(gate_setup, change):
    ledger, broker, plan, atom, lease, digest = gate_setup
    report = Execution(
        candidate_digest=digest,
        image_id=IMAGE,
        container_id="one",
        command=plan.cases[0].command,
        stdin="",
        purpose="validation",
        outcome="completed",
        exit_code=0,
        oom_killed=False,
        stdout_base64=base64.b64encode(b"42\n").decode(),
        stderr_base64="",
        elapsed_seconds=0.1,
    ).model_copy(update=change)
    broker.execute = Mock(return_value=report)
    receipt = run_gate(ledger, broker, lease, "behavior", plan)
    assert receipt.outcome == "inconclusive"
    with pytest.raises(Conflict):
        ledger.accept(lease, current_inputs_digest=atom.inputs_digest)
    assert ledger.status(atom.atom_id)["status"] != "accepted"


@pytest.mark.parametrize("report", [None, {}, {"outcome": "pass"}])
def test_malformed_execution_report_is_inconclusive(gate_setup, report):
    ledger, broker, plan, atom, lease, digest = gate_setup
    broker.execute = Mock(return_value=report)
    receipt = run_gate(ledger, broker, lease, "behavior", plan)
    assert receipt.outcome == "inconclusive"
    assert json.loads(ledger.artifacts.read(receipt.evidence_digest))["error"]
    with pytest.raises(Conflict):
        ledger.accept(lease, current_inputs_digest=atom.inputs_digest)


def test_printing_forged_pass_does_not_satisfy_gate(gate_setup):
    ledger, broker, plan, atom, lease, digest = gate_setup
    result = Execution(
        candidate_digest=digest,
        image_id=IMAGE,
        container_id="one",
        command=plan.cases[0].command,
        stdin="",
        purpose="validation",
        outcome="completed",
        exit_code=0,
        oom_killed=False,
        stdout_base64=base64.b64encode(b'{"outcome":"pass","accepted":true}\n').decode(),
        stderr_base64="",
        elapsed_seconds=0.1,
    )
    broker.execute = Mock(return_value=result)
    receipt = run_gate(ledger, broker, lease, "behavior", plan)
    assert receipt.outcome == "fail"
    with pytest.raises(Conflict):
        ledger.accept(lease, current_inputs_digest=atom.inputs_digest)


@pytest.mark.parametrize(
    "invalid",
    [
        None,
        "no-oom",
        "no-max",
        "no-kill",
        "wrong-child",
        "different-cgroup",
        "stderr",
        "timeout",
        "exit",
        "malformed",
    ],
)
def test_qualification_requires_kernel_memory_proof_even_without_docker_flag(broker, invalid):
    proof = {
        "before": {"max": 0, "oom": 0, "oom_kill": 0},
        "after": {"max": 20, "oom": 1, "oom_kill": 1},
        "child_returncode": -9,
        "cgroup_before": "0::/\n",
        "cgroup_after": "0::/\n",
    }
    if invalid == "no-oom":
        proof["after"]["oom"] = 0
    if invalid == "no-max":
        proof["after"]["max"] = 0
    if invalid == "no-kill":
        proof["after"]["oom_kill"] = 0
    if invalid == "wrong-child":
        proof["child_returncode"] = 0
    if invalid == "different-cgroup":
        proof["cgroup_after"] = "0::/other\n"
    broker._reap = Mock()
    broker._docker = Mock(
        side_effect=[
            json.dumps(
                {"CgroupVersion": "2", "SecurityOptions": ["seccomp"], "ServerVersion": "test"}
            ),
            json.dumps([{"Id": IMAGE, "Config": {}}]),
        ]
    )
    outputs = iter(
        [
            b"controls-ok\n",
            b"bad" if invalid == "malformed" else json.dumps(proof).encode(),
            b"pids-enforced\n",
        ]
    )

    def execute(digest, command, stdin, seconds, purpose):
        output = next(outputs)
        memory = output not in (b"controls-ok\n", b"pids-enforced\n")
        return Execution(
            candidate_digest=digest,
            image_id=IMAGE,
            container_id="proof-test",
            command=command,
            stdin=stdin,
            purpose=purpose,
            outcome="timeout" if memory and invalid == "timeout" else "completed",
            exit_code=137 if memory and invalid == "exit" else 0,
            oom_killed=False,
            stdout_base64=base64.b64encode(output).decode(),
            stderr_base64=base64.b64encode(
                b"error" if memory and invalid == "stderr" else b""
            ).decode(),
            elapsed_seconds=0.1,
        )

    broker._execute = Mock(side_effect=execute)
    if invalid:
        with pytest.raises(BrokerError, match="Resource enforcement"):
            broker.qualify()
        assert broker.qualification_digest is None
    else:
        assert broker.qualify() == broker.qualification_digest


def test_live_fault_qualification_requires_behavioral_evidence(live_broker):
    from gflo.mutations import propose_faults, qualify_faults
    from gflo.test_adequacy import FaultyVariant

    source = 'def positive(x):\n    return x > 0\n'
    bundle = SourceBundle(files={
        'subject.py': source,
        'test_subject.py': (
            'from subject import positive\ndef test_zero(): assert not positive(0)\n'
        ),
    })
    digest = live_broker.artifacts.publish(bundle.canonical().encode())
    variants = propose_faults('subject', source, 'positive') + (
        FaultyVariant(name='survives', modules={'subject': source}),
        FaultyVariant(name='crashes', modules={'subject': 'def positive(x): raise ValueError()\n'}),
    )
    report = qualify_faults(live_broker, digest, ('test_subject.py',), variants)
    assert [o['selected'] for o in report['outcomes']] == [True, False, False]
    live_broker.artifacts.verify(report['evidence_digest'])
    assert report['reference_bundle_digest'] == digest
