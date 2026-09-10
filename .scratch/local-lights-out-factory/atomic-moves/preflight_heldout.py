"""Qualify the held-out real commit failure against original and reference code."""

import importlib.util
import json
from pathlib import Path

from gflo.broker import DockerBroker, SourceBundle
from gflo.ledger import WorkLedger

here = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("campaign", here / "campaign.py")
assert spec and spec.loader
campaign = importlib.util.module_from_spec(spec)
spec.loader.exec_module(campaign)
fixture = json.loads((campaign.ROOT / "trial-1/fixture.json").read_text())
files = {p: (campaign.TARGET / p).read_text() for p in campaign.EXECUTION}
original = files[campaign.IMPLEMENTATION]
rows = []
output = campaign.ROOT / "heldout-preflight.json"
assert not output.exists()
with WorkLedger(campaign.ROOT / "heldout-preflight-v2.db") as ledger:
    broker = DockerBroker(ledger.artifacts, fixture["request"]["environments"]["python"]["image"])
    broker.qualify()
    for name, text, expected in [
        ("original", original, False),
        (
            "reference",
            campaign.replace_method(original, (here / "reference-method.py").read_text()),
            True,
        ),
    ]:
        bundle = SourceBundle(files=files | {campaign.IMPLEMENTATION: text})
        digest = ledger.artifacts.publish(bundle.canonical().encode())
        execution = broker.execute(
            digest,
            ("python", "-B", "-c", (here / "heldout.py").read_text()),
            seconds=30,
            purpose="validation",
        )
        rows.append(
            dict(name=name, expected_pass=expected, execution=execution.model_dump(mode="json"))
        )
        output.write_text(json.dumps(rows, indent=2) + "\n")
        print(name, execution.exit_code, flush=True)
        assert (execution.exit_code == 0) == expected
