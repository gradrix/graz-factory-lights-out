"""Recreate a fresh supervised window trial on the pinned local deployment."""
import argparse
import json
from pathlib import Path

from gflo.autonomy import FeaturePolicy, build_feature
from gflo.broker import SourceBundle
from gflo.ledger import WorkLedger
from gflo.model import ModelProfile
from gflo.planning import FeatureRequest, RepositoryFeatureRequest, draft_feature
from gflo.repository import snapshot_bundle


def source_bundle():
    text = (''.join(f'constant_{i} = {i}\n' for i in range(5000))
            + 'def chosen_value():\n    return 41\n'
            + ''.join(f'constant_{i} = {i}\n' for i in range(5000, 10000)))
    return SourceBundle(files={
        'large.py': text,
        'consumer.py': 'from large import chosen_value\ndef render(value):\n'
                       '    return "value=" + str(chosen_value(value))\n',
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixture', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    fixture = json.loads(args.fixture.read_text())
    source = source_bundle()
    if fixture.get('mode') == 'planning':
        fields = dict(fixture['request'], source=source.model_dump(mode='json'))
        request = FeatureRequest.model_validate_json(json.dumps(fields))
        assert request.digest() == fixture['request_digest']
        result = draft_feature(request, ModelProfile.model_validate_json(
            json.dumps(fixture['profile'])), args.output,
            deployment=fixture['deployment'], structured_interfaces=True)
    else:
        request = RepositoryFeatureRequest.model_validate_json(json.dumps(fixture['request']))
        policy = FeaturePolicy.model_validate_json(json.dumps(fixture['policy']))
        args.output.mkdir(parents=True, exist_ok=False)
        with WorkLedger(args.output / 'ledger.db') as ledger:
            assert snapshot_bundle(ledger.artifacts, source) == request.source
            result = build_feature(ledger, request, policy, args.output / 'build',
                                   lambda: request.source)
    print(json.dumps({'status': result['status'], 'output': str(args.output)}))


if __name__ == '__main__':
    main()
