#!/usr/bin/env python3
"""Prepare disposable supplemental-probe controls; never import/execute candidate code."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def files(root):
    result = {}
    for path in sorted(root.rglob('*')):
        if path.is_symlink(): raise ValueError('Control source links unsupported')
        if path.is_file(): result[str(path.relative_to(root))] = sha(path)
    return result


def replace(root, relative, old, new):
    path = root / relative
    text = path.read_text()
    if text.count(old) != 1: raise ValueError('Reference mutation anchor changed: ' + relative)
    path.write_text(text.replace(old, new, 1))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--reference-manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    reference = args.reference.resolve()
    original = files(reference)
    hashes = json.loads(args.reference_manifest.read_bytes())
    prefix = 'private/references/config-preview/'
    expected = {name[len(prefix):]: value for name, value in hashes.items() if name.startswith(prefix)}
    if not expected or original != expected: raise ValueError('Frozen private reference changed')
    args.output.mkdir(mode=0o700)  # Never overwrite previous evidence/candidates.
    variants = [
        ('conforming', None, [], []),
        ('scalar-depth-mutant', ('src/config_preview/validation.py',
            "if count>200 or depth>6:raise ValueError('limit')",
            "if count>200 or (isinstance(v,dict) and depth>6):raise ValueError('limit')"),
            ['API/depth7-base', 'API/insert-valid-value-exceeds-total-depth',
             'HTTP/depth7-base', 'HTTP/insert-valid-value-exceeds-total-depth'],
            ['API/depth6-at-limit', 'HTTP/depth6-at-limit']),
        ('missing-body-mutant', ('src/config_preview/routes.py',
            'def config_preview(payload=Body(...)):', 'def config_preview(payload):'),
            ['HTTP/depth6-at-limit', 'HTTP/stateless-after-conflicts'],
            ['API/depth6-at-limit', 'API/audit-snapshots-and-input-aliasing']),
        ('validation-order-mutant', ('src/config_preview/domain.py',
            'request(base,operations);result=copy.deepcopy(base);audit=[]',
            'request(base,[]);result=copy.deepcopy(base);audit=[]'),
            ['API/late-invalid-preempts-conflict', 'HTTP/late-invalid-preempts-conflict',
             'API/late-node-overflow-preempts-conflict', 'HTTP/late-node-overflow-preempts-conflict'],
            ['API/nested-exact-test-key-order', 'HTTP/nested-exact-test-key-order']),
    ]
    receipt = {'reference_manifest_sha256': sha(args.reference_manifest), 'reference_files': original,
               'probe_sha256': sha(Path(__file__).with_name('qa-api-probes.py')), 'variants': {}}
    for name, mutation, required_failures, required_passes in variants:
        destination = args.output / name
        shutil.copytree(reference, destination)
        if mutation: replace(destination, *mutation)
        if name == 'validation-order-mutant':
            replace(destination, 'src/config_preview/domain.py',
                    'for index,item in enumerate(operations):\n        parent=result',
                    'for index,item in enumerate(operations):\n        request({},[item])\n        parent=result')
        receipt['variants'][name] = {'files': files(destination),
            'expected_exit': 0 if mutation is None else 1,
            'required_failed_probes': required_failures, 'required_passed_probes': required_passes,
            'all_probes_must_pass': mutation is None}
    if files(reference) != original: raise ValueError('Original reference changed during preparation')
    (args.output / 'manifest.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'prepared': str(args.output), 'manifest_sha256': sha(args.output / 'manifest.json'),
                      'executed': False}))


if __name__ == '__main__': main()
