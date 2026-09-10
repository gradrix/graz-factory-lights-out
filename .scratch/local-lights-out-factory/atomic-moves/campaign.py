"""Three frozen stateful real-repository feature builds on the pinned local model."""

# Preserve the exact frozen validator and requirement strings.
# ruff: noqa: E501
import argparse
import ast
import base64
import json
import subprocess
from pathlib import Path

from gflo.autonomy import FeaturePolicy, build_feature
from gflo.broker import DockerBroker, SourceBundle
from gflo.gates import ProcessCase, ProcessGate
from gflo.ledger import WorkLedger
from gflo.model import ModelProfile
from gflo.planning import RepositoryFeatureRequest
from gflo.records import ContextBudget
from gflo.repository import Repository, SnapshotSource, capture_worktree

HERE = Path(__file__).resolve().parent
ROOT = Path(".gflo/evidence/atomic-moves-v2")
TARGET = Path(".gflo/targets/ai-gamer-atomic-baseline")
REVISION = "9a0a4384b9b727c02f0f2c168c7abc43a4e076bf"
IMPLEMENTATION = "game_server/state/recorderdb.py"
TEST = "tests/test_atomic_moves.py"
WINNER_TEST = "tests/test_winner_windows.py"
SCHEMA = "game_server/state/game_records_schema.sql"
EXECUTION = (
    IMPLEMENTATION,
    SCHEMA,
    "game_server/state/gamestatemanager.py",
    "game_server/games/ticktaktoe.py",
    WINNER_TEST,
    "common/__init__.py",
    "common/models/__init__.py",
    "common/models/game.py",
    "common/models/move.py",
    "common/models/player.py",
    "common/models/enums.py",
    "common/models/gamebase.py",
    "common/timehelpers.py",
    "game_server/__init__.py",
)


def replace_method(text, method):
    cls = next(
        n for n in ast.parse(text).body if isinstance(n, ast.ClassDef) and n.name == "RecorderDb"
    )
    node = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "addMoves")
    lines = text.splitlines(keepends=True)
    return "".join(lines[: node.lineno - 1]) + method + "".join(lines[node.end_lineno :])


def gates(original):
    reference = (HERE / "reference-method.py").read_text()
    variants = {
        "original": original,
        "wrong-index": replace_method(
            original, reference.replace("playerid, idx,", "playerid, move.idx,")
        ),
        "wrong-error-return": replace_method(
            original, reference.replace("return -1", "return True")
        ),
        "missing-commit": replace_method(
            original, reference.replace("                self.conn.commit()\n", "")
        ),
    }
    preserve = """import ast
from pathlib import Path
current=Path(PATH).read_text()
original=ORIGINAL
def outside(text):
    module=ast.parse(text)
    cls=next(n for n in module.body if isinstance(n,ast.ClassDef) and n.name=='RecorderDb')
    cls.body=[n for n in cls.body if not (isinstance(n,ast.FunctionDef) and n.name=='addMoves')]
    return ast.dump(module)
assert outside(current)==outside(original), 'unrelated code changed'
""".replace("PATH", repr(IMPLEMENTATION)).replace("ORIGINAL", repr(original))
    oracle = preserve + "\n" + (HERE / "oracle.py").read_text()
    tests = (
        """import hashlib,subprocess,sys,tempfile,xml.etree.ElementTree as ET
from pathlib import Path
variants=VARIANTS
runner=RUNNER
original={p:Path(p).read_text() for p in PATHS}
for name,text in [('candidate',original[IMPL])]+list(variants.items()):
    expected=dict(original);expected[IMPL]=text
    Path(IMPL).write_text(text)
    with tempfile.TemporaryDirectory() as d:
        xml=Path(d)/'report.xml'
        result=subprocess.run([sys.executable,'-B','-c',runner,'-q','-p','no:cacheprovider','--junitxml='+str(xml),TESTPATH],capture_output=True,text=True)
        assert xml.exists(), (name,result.stdout,result.stderr)
        tree=ET.parse(xml)
        cases=tree.findall('.//testcase')
        failures=tree.findall('.//failure')
        assert len(cases)>=5 and not tree.findall('.//error') and not tree.findall('.//skipped'), (name,result.stdout,result.stderr)
        if name=='candidate':assert result.returncode==0,(name,result.stdout,result.stderr)
        else:
            assert result.returncode==1 and failures,(name,result.stdout,result.stderr)
    assert {p:Path(p).read_text() for p in original}==expected, 'tests modified production source'
for p,text in original.items():Path(p).write_text(text)
print('atomic-tests-qualified')
""".replace("VARIANTS", repr(variants))
        .replace(
            "RUNNER",
            "'import pytest,sys\\nclass Audit:\\n    bad_exception=False\\n    def pytest_runtest_makereport(self,item,call):\\n        if call.excinfo and not issubclass(call.excinfo.type,(AssertionError,pytest.fail.Exception)):\\n            self.bad_exception=True\\nplugin=Audit()\\ncode=pytest.main(sys.argv[1:],plugins=[plugin])\\nsys.exit(99 if plugin.bad_exception else code)\\n'",
        )
        .replace("PATHS", repr(EXECUTION))
        .replace("IMPL", repr(IMPLEMENTATION))
        .replace("TESTPATH", repr(TEST))
    )
    regression = """import subprocess,sys
r=subprocess.run([sys.executable,'-B','-m','pytest','-q','-p','no:cacheprovider',TEST,WINNER],capture_output=True,text=True)
assert r.returncode==0,(r.stdout,r.stderr)
print('existing-and-new-tests-qualified')
""".replace("TEST", repr(TEST)).replace("WINNER", repr(WINNER_TEST))

    def gate(code, output):
        return ProcessGate(
            cases=(
                ProcessCase(
                    command=("python", "-B", "-c", code), expected_stdout=output + "\n", seconds=30
                ),
            )
        )

    return (
        gate(oracle, "atomic-moves-qualified"),
        gate(tests, "atomic-tests-qualified"),
        gate(regression, "existing-and-new-tests-qualified"),
        variants,
    )


def main():
    global ROOT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT)
    args = parser.parse_args()
    ROOT = args.output
    assert (
        subprocess.check_output(["git", "-C", str(TARGET), "rev-parse", "HEAD"], text=True).strip()
        == REVISION
    )
    assert not subprocess.check_output(
        ["git", "-C", str(TARGET), "status", "--porcelain"], text=True
    ).strip()
    ROOT.mkdir(parents=True, exist_ok=False)
    profile = json.loads((HERE.parent / "test-decomposition/fixture.json").read_text())
    original = (TARGET / IMPLEMENTATION).read_text()
    behavior, tests, regression, variants = gates(original)
    policies = []
    for name in ("trial-1", "trial-2", "trial-3"):
        output = ROOT / name
        output.mkdir()
        with WorkLedger(output / "ledger.db") as ledger:
            source = capture_worktree(ledger.artifacts, TARGET)
            request = RepositoryFeatureRequest(
                feature_id="ai-gamer-atomic-moves-" + name,
                objective="Make recording move batches atomic so failed game-history writes cannot leak partial moves into later commits; add real SQLite regression tests.",
                requirements={
                    "atomicity": "Change only RecorderDb.addMoves in game_server/state/recorderdb.py. A SQLite Error during batch insertion or commit returns -1 and rolls back all rows from that batch before releasing self.lock. Preserve already committed rows; leave no pending failed transaction. Subsequent database writes and successful retries work. Success, including an empty batch, commits and returns True. Preserve stored gameid/playerid/move/date; idx remains enumerate order starting at zero rather than Move.idx. Keep schema, other methods and public signature unchanged. Use existing sqlite3 and threading facilities, no new dependencies.",
                    "tests": "Add tests/test_atomic_moves.py with at least five collected substantive pytest cases using the real RecorderDb, real SQLite and real schema. Configure recorderdb.RECORDER_DB to a temporary database path; do not use production data or stub the database. Cover committed successful rows and enumerated indices/date, an empty batch, first and later row constraint failures, rollback preserving prior committed rows, and recovery including a later unrelated write. Tests must pass correct code and detect missing rollback, wrong indices, wrong error return, and missing commit through assertions. No skips, fake imports or replacement database implementations.",
                },
                source=source,
                allowed_paths=(IMPLEMENTATION, TEST),
                environments={
                    "python": {
                        "image": profile["image"],
                        "description": "Pinned Python, SQLite and pytest",
                    }
                },
            )
            policy = FeaturePolicy(
                request_digest=request.digest(),
                file_gates={IMPLEMENTATION: behavior, TEST: tests},
                execution_paths=EXECUTION + (TEST,),
                planning_paths=(
                    IMPLEMENTATION,
                    "common/models/move.py",
                    SCHEMA,
                    "game_server/state/gamestatemanager.py",
                ),
                integration_gates={"behavior": behavior, "tests": tests, "regression": regression},
                environment_id="python",
                model_profile=ModelProfile.model_validate_json(json.dumps(profile["profile"])),
                deployment=profile["deployment"],
                context_budget=ContextBudget(total_tokens=12288, output_tokens=4096),
                max_tasks=3,
                max_attempts=2,
                max_model_turns=3,
            )
            (output / "fixture.json").write_text(
                json.dumps(
                    dict(
                        revision=REVISION,
                        request=request.model_dump(mode="json"),
                        policy=policy.model_dump(mode="json"),
                    ),
                    indent=2,
                )
                + "\n"
            )
            if ROOT.name != "atomic-moves-v2":
                prior = json.loads(
                    (Path(".gflo/evidence/atomic-moves-v2") / name / "fixture.json").read_text()
                )
                assert request.model_dump(mode="json") == prior["request"]
                assert policy.model_dump(mode="json") == prior["policy"]
            policies.append((output, request, policy))
    # Validate the reference, the old failing implementation and every frozen test fault.
    output, request, policy = policies[0]
    with WorkLedger(output / "ledger.db") as ledger:
        repo = Repository(SnapshotSource(ledger.artifacts, request.source))
        source = repo.select(EXECUTION, purpose="execution").bundle
        good = SourceBundle(
            files=source.files
            | {
                IMPLEMENTATION: replace_method(
                    original, (HERE / "reference-method.py").read_text()
                ),
                TEST: (HERE / "reference-tests.py").read_text(),
            }
        )
        broker = DockerBroker(ledger.artifacts, profile["image"])
        broker.qualify()
        rows = []
        for label, bundle, gate, expected in [
            ("reference-behavior", good, behavior, True),
            ("reference-tests", good, tests, True),
            ("reference-regression", good, regression, True),
        ] + [
            (name, SourceBundle(files=good.files | {IMPLEMENTATION: text}), behavior, False)
            for name, text in variants.items()
        ]:
            digest = ledger.artifacts.publish(bundle.canonical().encode())
            case = gate.cases[0]
            executed = broker.execute(
                digest, case.command, seconds=case.seconds, purpose="validation"
            )
            rows.append(
                dict(name=label, expected_pass=expected, execution=executed.model_dump(mode="json"))
            )
            (ROOT / "preflight.json").write_text(json.dumps(rows, indent=2) + "\n")
            assert (executed.exit_code == 0) == expected, (
                label,
                executed.exit_code,
                base64.b64decode(executed.stderr_base64).decode()[-2000:],
            )
        print("preflight passed", flush=True)
    for output, request, policy in policies:
        with WorkLedger(output / "ledger.db") as ledger:
            result = build_feature(
                ledger, request, policy, output / "build", lambda: request.source
            )
            print(output.name, result["status"], flush=True)


if __name__ == "__main__":
    main()
