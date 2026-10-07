"""Build review cohort 2 from coding-d references plus single seeded defects. Run once; output is frozen by manifest."""
import hashlib, json, pathlib, shutil
root = pathlib.Path(__file__).resolve().parents[1]
evals = root.parent
coding = evals / 'coding-d'
known = evals / 'executable-review'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

# (task, split, kind, file, old, new, required finding) — kind 'original' carries one seeded objective violation.
SEEDS = {
    '01': ('dev', 'cli.py', "  print(str(error),file=sys.stderr);return 2", "  raise",
           'CLI ValueError path raises a traceback and exits 1 instead of exit 2 with stderr and no traceback'),
    '05': ('dev', 'domain.py', "last={c['id']:i for i,c in enumerate(p['changes'])}",
           "last={};[last.setdefault(c['id'],i) for i,c in enumerate(p['changes'])]",
           'Deduplication retains the FIRST occurrence instead of the LAST'),
    '06': ('holdout', 'domain.py', "b['id']<old['id']", "b['id']>old['id']",
           'Identical-timestamp tie keeps the largest id instead of the smallest'),
    '09': ('holdout', 'README.md', '{"action": "export", "invoices"', '{"action": "export_csv", "invoices"',
           'README concrete CLI invocation uses a nonexistent action and fails'),
    '10': ('holdout', 'domain.py', None, None, 'blockers are not sorted by Python string order'),
    '12': ('holdout', 'domain.py', " if not eligible:return None",
           " p['artifacts'].sort(key=lambda a:a['id'])\n if not eligible:return None",
           'select mutates the input artifacts list (sorts it in place)'),
}
CONTROLS = {'02': 'dev', '03': 'dev', '04': 'holdout', '07': 'holdout', '08': 'holdout', '11': 'holdout'}

public = root / 'public'
assert not public.exists()
cases, expectations = [], []

def add(identifier, split, kind, source_dir, objective, expected, finding, origin):
    case = public / identifier
    shutil.copytree(source_dir, case / 'source')
    (case / 'objective.txt').write_text(objective)
    cases.append({'id': identifier, 'source': f'public/{identifier}/source', 'objective': f'public/{identifier}/objective.txt', 'profile': 'python-stdlib'})
    expectations.append({'id': identifier, 'split': split, 'kind': kind, 'expected': expected, 'required_finding': finding, 'origin': origin})

# Known cases from cohort 1 (dev regression; already used for tuning).
known_expect = {e['id']: e for e in json.loads((known / 'private/expectations.json').read_text())}
for case in json.loads((known / 'manifest.json').read_text())['cases']:
    e = known_expect[case['id']]
    add('k' + case['id'][-2:], 'dev', e['kind'], known / case['source'], (known / case['objective']).read_text(),
        e['expected'], e['required_finding'], 'executable-review/' + case['id'])

import tempfile
for task_dir in sorted((coding / 'tasks').iterdir()):
    number = task_dir.name[:2]
    task = json.loads((task_dir / 'task.json').read_text())
    files = json.loads((coding / 'private' / f'{number}-reference.json').read_text())
    if number in SEEDS:
        split, name, old, new, finding = SEEDS[number]
        if number == '10':
            text = files[name]
            for a, b in [("block=set()", "block={}"), ("block.add(s)", "block[s]=1"), ("sorted(block)", "list(block)")]:
                assert a in text; text = text.replace(a, b)
            files[name] = text
        else:
            assert files[name].count(old) == 1, (number, old)
            files[name] = files[name].replace(old, new)
        kind, expected = 'original', 'repair'
    else:
        split, finding, kind, expected = CONTROLS[number], None, 'control', 'pass'
    with tempfile.TemporaryDirectory() as tmp:
        work = pathlib.Path(tmp) / 'source'
        shutil.copytree(task_dir / 'source', work)
        for name, content in files.items():
            (work / name).write_text(content)
        add('d' + number, split, kind, work, task['objective'] + '\n', expected, finding, 'coding-d/' + task_dir.name)

paths = sorted(public.rglob('*'))
for p in paths:
    p.chmod(0o755 if p.is_dir() else 0o644)
manifest = {'version': 1, 'cohort': 'review-cohort-2', 'cases': cases,
            'files': {str(p.relative_to(root)): sha(p) for p in paths if p.is_file()},
            'modes': {str(p.relative_to(root)): p.stat().st_mode & 0o777 for p in paths}}
(root / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
(root / 'private/expectations.json').write_text(json.dumps(expectations, indent=2) + '\n')
print(sha(root / 'manifest.json'), len(cases))
