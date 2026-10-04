"""Offline comparison of preserved actual records; no original writes or model access."""
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def hashes(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file() and p.name != '.lock'}


if len(sys.argv) > 1:
    from gflo import documents
    assert Path(documents.__file__).is_relative_to(Path(sys.argv[2]))
    root = Path(sys.argv[1])
    result = []
    for store_path in sorted(root.glob('store-*')):
        store = documents.DocumentStore(store_path, executor=lambda *a, **k: (_ for _ in ()).throw(AssertionError('Offline executor')))
        for path in sorted(store_path.iterdir()):
            if not path.is_dir():
                continue
            saved = store.resolve(path.name)
            saved.pop('age_seconds', None)
            row = {'store': store_path.name, 'id': path.name, 'resolved': saved}
            if saved['receipt']['kind'] != 'evidence':
                try:
                    row['replay'] = store.replay(path.name)
                    row['replay'].pop('age_seconds', None)
                except ValueError as error:
                    row['replay_error'] = str(error)
            result.append(row)
    print(json.dumps(result, sort_keys=True))
else:
    root = Path('.gflo/document-reference-builder').resolve()
    sources = ['.gflo/document-reliability-trial1/store', '.gflo/document-research-cohort/json/store', '.gflo/document-research-cohort/csv/store']
    originals = {source: hashes(Path(source)) for source in sources}
    for number, source in enumerate(sources):
        destination = root / f'store-{number}'
        shutil.copytree(source, destination)
        destination.chmod(0o700)
    before = hashes(root)
    outputs = []
    for name, source in [('old', root / 'legacy-source'), ('new', Path.cwd())]:
        raw = subprocess.check_output([sys.executable, str(Path(__file__).resolve()), str(root), str(source)],
                                      env=dict(os.environ, PYTHONPATH=str(source)))
        (root / f'{name}-replay.json').write_bytes(raw)
        outputs.append(json.loads(raw))
    assert outputs[0] == outputs[1]
    assert all(originals[s] == hashes(Path(s)) for s in sources)
    after = hashes(root)
    assert all(after[p] == h for p, h in before.items())
    frozen = (root / 'legacy-source/gflo/documents.py').read_text()
    current = Path('gflo/documents.py').read_text()
    def functions(text):
        return {n.name: ast.get_source_segment(text, n) for n in ast.parse(text).body if isinstance(n, ast.FunctionDef)}
    old, new = functions(frozen), functions(current)
    same = {}
    for name in ['validate_answer', 'answer_request', 'repair_request', 'response_answer']:
        assert old[name] == new[name], name
        same[name] = hashlib.sha256(old[name].encode()).hexdigest()
    summary = {'records': len(outputs[1]), 'by_format_kind': {}, 'same_legacy_helpers': same,
               'original_and_copied_record_hashes_unchanged': True,
               'resolved_and_replayed_equal_excluding_age_seconds': True}
    for row in outputs[1]:
        receipt = row['resolved']['receipt']
        key = str(receipt['format']) + ':' + receipt['kind']
        summary['by_format_kind'][key] = summary['by_format_kind'].get(key, 0) + 1
    Path('.scratch/.sflo/07-autonomy-document-references/builder-legacy.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))
