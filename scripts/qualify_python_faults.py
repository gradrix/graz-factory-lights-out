#!/usr/bin/env python3
"""Generate and sandbox-qualify Python faults from an operator-owned fixture."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from gflo.artifacts import ArtifactStore
from gflo.broker import DockerBroker
from gflo.mutations import propose_faults, qualify_faults
from gflo.worker import SourceBundle


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixture', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    fixture = json.loads(args.fixture.read_bytes())
    bundle = SourceBundle.model_validate_json(json.dumps(fixture['reference_bundle']))
    source = bundle.files[fixture['source_path']]
    variants = propose_faults(fixture['module'], source, fixture['function'])
    if not variants:
        raise ValueError('No supported mutation sites in the selected function')
    args.output.mkdir(parents=True, exist_ok=False)
    broker = DockerBroker(ArtifactStore(args.output / 'artifacts'), fixture['image'])
    digest = broker.artifacts.publish(bundle.canonical().encode())
    broker.qualify()
    report = qualify_faults(broker, digest, tuple(fixture['tests']), variants)
    (args.output / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'evidence_digest': report['evidence_digest'],
                      'selected': sum(o['selected'] for o in report['outcomes']),
                      'proposed': len(variants)}, indent=2))


if __name__ == '__main__':
    main()
