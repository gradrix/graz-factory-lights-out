"""Frozen fresh-run qualification for retained window planner workloads."""

import argparse
import importlib.util
import json
from pathlib import Path

from gflo.autonomy import FeaturePolicy, build_feature
from gflo.ledger import WorkLedger
from gflo.model import ModelProfile
from gflo.planning import FeatureRequest, RepositoryFeatureRequest, draft_feature
from gflo.repository import snapshot_bundle

BASE = Path(__file__).parent.parent / "window-feature-qualification"
spec = importlib.util.spec_from_file_location("window_fixture", BASE / "reproduce.py")
fixture_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture_module)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.output
    root.mkdir(parents=True, exist_ok=False)
    schedule = [
        (kind + "-" + str(i), kind) for i in range(1, 4) for kind in ["navigation", "feature"]
    ]
    (root / "schedule.json").write_text(json.dumps(schedule) + "\n")
    for name, kind in schedule:
        output = root / name
        source = fixture_module.source_bundle()
        if kind == "navigation":
            data = json.loads((BASE / "window-planner-navigation-v3-fixture.json").read_text())
            request = FeatureRequest.model_validate_json(
                json.dumps(dict(data["request"], source=source.model_dump(mode="json")))
            )
            assert request.digest() == data["request_digest"]
            result = draft_feature(
                request,
                ModelProfile.model_validate_json(json.dumps(data["profile"])),
                output,
                deployment=data["deployment"],
                structured_interfaces=True,
            )
            print(name, result["status"], flush=True)
        else:
            data = json.loads((BASE / "window-feature-v4-fixture.json").read_text())
            request = RepositoryFeatureRequest.model_validate_json(json.dumps(data["request"]))
            policy = FeaturePolicy.model_validate_json(json.dumps(data["policy"]))
            output.mkdir()
            with WorkLedger(output / "ledger.db") as ledger:
                assert snapshot_bundle(ledger.artifacts, source) == request.source
                result = build_feature(
                    ledger, request, policy, output / "build", lambda: request.source
                )
            print(name, result["status"], flush=True)


if __name__ == "__main__":
    main()
