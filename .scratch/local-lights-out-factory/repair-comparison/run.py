"""Small matched-input diagnostic; not a model deployment qualification."""

import fcntl
import json
import sys
import time
import urllib.request
from pathlib import Path

from probe import HERE, IMAGE, IMPORT, SOURCE, check

from gflo.autonomy import FeaturePolicy, build_feature
from gflo.broker import SourceBundle
from gflo.ledger import WorkLedger
from gflo.model import LocalModel, ModelProfile
from gflo.planning import RepositoryFeatureRequest
from gflo.qualification import prepared_planner
from gflo.repository import snapshot_bundle

sys.path.insert(0, str(IMPORT))
from prepared_campaign import make_proposal

ROOT = Path(".gflo/evidence/repair-comparison-v2")
fixture = json.loads((IMPORT / "resume-fixture.json").read_text())
requirement = fixture["request"]["requirements"]["tabular"]
profile = ModelProfile.model_validate(fixture["policy"]["model_profile"])


def post(path, payload):
    req = urllib.request.Request(
        profile.base_url.removesuffix("/v1") + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as response:
        return json.load(response)


def main():
    ROOT.mkdir(parents=True, exist_ok=False)
    schedule = dict(
        model_profile=profile.model_dump(mode="json"),
        input_source=SOURCE,
        requirement=requirement,
        image=IMAGE,
        arms=["factory", "minimal"],
        max_responses_per_arm=6,
        total_tokens_per_response=16384,
        output_tokens=6144,
        note=(
            "Same starting parser, requirement, broker gate, model, seed and per-call budgets. "
            "Whole-file minimal JSON versus factory windows/exact edits; "
            "composite contrast, not single-variable causality."
        ),
    )
    (ROOT / "schedule.json").write_text(json.dumps(schedule, indent=2) + "\n")
    (HERE / "schedule.json").write_text(json.dumps(schedule, indent=2) + "\n")
    path = ROOT / "factory"
    path.mkdir()
    with WorkLedger(path / "ledger.db") as ledger:
        files = {
            "tabular.py": SOURCE,
            "BRIEF.md": requirement,
            "ENVIRONMENT.md": "Python standard library; offline isolated execution.\n",
        }
        request = RepositoryFeatureRequest.model_validate_json(
            json.dumps(fixture["request"])
        ).model_copy(
            update={
                "feature_id": "parser-repair-comparison",
                "objective": (
                    "Repair tabular.py to satisfy the complete CSV requirement. "
                    "Preserve working behavior."
                ),
                "requirements": {"tabular": requirement},
                "source": snapshot_bundle(ledger.artifacts, SourceBundle(files=files)),
                "allowed_paths": ("tabular.py",),
            }
        )
        policy = FeaturePolicy.model_validate_json(json.dumps(fixture["policy"]))
        gate = policy.file_gates["tabular.py"]
        policy = policy.model_copy(
            update={
                "request_digest": request.digest(),
                "file_gates": {"tabular.py": gate},
                "integration_gates": {"tabular": gate},
                "execution_paths": tuple(files),
                "planning_paths": ("BRIEF.md", "ENVIRONMENT.md"),
                "max_tasks": 1,
                "max_reserved_tokens": 172032,
            }
        )
        request = RepositoryFeatureRequest.model_validate_json(request.canonical())
        policy = FeaturePolicy.model_validate_json(policy.canonical())
        proposal = make_proposal(request)
        (path / "fixture.json").write_text(
            json.dumps(
                dict(
                    request=request.model_dump(mode="json"),
                    policy=policy.model_dump(mode="json"),
                    proposal=proposal.model_dump(mode="json"),
                ),
                indent=2,
            )
            + "\n"
        )
        result = build_feature(
            ledger,
            request,
            policy,
            path / "build",
            lambda: request.source,
            planner=prepared_planner(proposal),
        )
        summary = {"factory": {"status": result["status"]}}
        print("factory", result["status"], flush=True)
    path = ROOT / "minimal"
    path.mkdir()
    with WorkLedger(path / "ledger.db") as ledger:
        model = LocalModel(ledger.artifacts, profile)
        current = SOURCE
        feedback = "Repair the retained failed implementation against the requirement."
        rows = []
        for turn in range(1, 7):
            chat = dict(
                model=profile.model,
                chat_template_kwargs={"enable_thinking": False},
                messages=[
                    {
                        "role": "system",
                        "content": (
                            'You repair Python code. Return only a JSON object with one key "code" '
                            "containing the complete corrected tabular.py. "
                            "Do not claim to run tests."
                        ),
                    },
                    {
                        "role": "user",
                        "content": requirement
                        + "\nCurrent tabular.py:\n"
                        + current
                        + "\nFeedback:\n"
                        + feedback,
                    },
                ],
            )
            with model.lock_path.open("a") as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                tokens = post("/tokenize", chat | {"add_generation_prompt": True})
                assert tokens["max_model_len"] == 16384 and tokens["count"] + 6144 <= 16384
                wire = chat | dict(
                    temperature=0,
                    seed=42,
                    max_tokens=6144,
                    response_format={"type": "json_object"},
                    stream=False,
                )
                (path / f"{turn}-request.json").write_text(json.dumps(wire, indent=2))
                start = time.monotonic()
                response = post("/v1/chat/completions", wire)
                elapsed = time.monotonic() - start
            (path / f"{turn}-response.json").write_text(json.dumps(response, indent=2))
            assert response["model"] == profile.model
            assert response["usage"]["prompt_tokens"] == tokens["count"]
            row = dict(turn=turn, usage=response["usage"], elapsed_seconds=elapsed)
            try:
                choice = response["choices"][0]
                assert choice["finish_reason"] == "stop", "incomplete output"
                parsed = json.loads(choice["message"]["content"])
                assert set(parsed) == {"code"} and isinstance(parsed["code"], str)
                current = parsed["code"]
                outcome = check(ledger, current)
                row.update(outcome)
                feedback = outcome["stderr"] or outcome["stdout"]
            except (AssertionError, ValueError, KeyError) as error:
                row.update(passed=False, protocol_error=str(error))
                feedback = (
                    "Invalid response: " + str(error) + ". Return complete valid JSON with code."
                )
            rows.append(row)
            (path / "results.json").write_text(json.dumps(rows, indent=2) + "\n")
            print("minimal", turn, row["passed"], flush=True)
            if row["passed"]:
                break
        summary["minimal"] = rows
    (HERE / "results.json").write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    main()
