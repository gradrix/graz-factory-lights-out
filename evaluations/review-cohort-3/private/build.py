"""Build review-cohort-3 public cases deterministically from coding-b/coding-c inputs.

Run inside Docker, e.g.:
  docker run --rm --user 1000:1000 --network none -v /home/gradrix/repos:/home/gradrix/repos \
    -w <cohort>/private python:3.12-slim python -B build.py
Refuses to run if public/ already exists.
"""
import hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
COHORT = os.path.dirname(HERE)
EVAL = os.path.dirname(COHORT)
PUBLIC = os.path.join(COHORT, 'public')
INPUTS = (('coding-b', 'b'), ('coding-c', 'c'))


def read_tree(root):
    files = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in ('.git', '__pycache__'))
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            with open(full, 'rb') as handle:
                files[os.path.relpath(full, root).replace(os.sep, '/')] = handle.read()
    return files


def reference(cohort, number):
    if cohort == 'coding-b':
        path = os.path.join(EVAL, cohort, 'private', 'references', number + '.json')
    else:
        path = os.path.join(EVAL, cohort, 'private', number + '-reference.json')
    with open(path, encoding='utf-8') as handle:
        mapping = json.load(handle)
    return {name: text.encode('utf-8') for name, text in mapping.items()}


def main():
    if os.path.exists(PUBLIC):
        sys.exit('refusing to build: public/ already exists')
    with open(os.path.join(HERE, 'expectations.json'), encoding='utf-8') as handle:
        expectations = {row['id']: row for row in json.load(handle)}
    cases = []
    for cohort, prefix in INPUTS:
        tasks_dir = os.path.join(EVAL, cohort, 'tasks')
        for task in sorted(os.listdir(tasks_dir)):
            number = task[:2]
            case_id = prefix + number
            row = expectations[case_id]
            assert row['origin'] == cohort + '/' + task, (case_id, row['origin'])
            with open(os.path.join(tasks_dir, task, 'task.json'), encoding='utf-8') as handle:
                objective = json.load(handle)['objective']
            files = read_tree(os.path.join(tasks_dir, task, 'source'))
            files.update(reference(cohort, number))
            for layer in ('completions', 'seeds'):
                layer_dir = os.path.join(HERE, layer, case_id)
                if os.path.isdir(layer_dir):
                    files.update(read_tree(layer_dir))
            seeded = os.path.isdir(os.path.join(HERE, 'seeds', case_id))
            assert seeded == (row['kind'] == 'original'), case_id
            assert (row['expected'] == 'repair') == seeded, case_id
            cases.append((case_id, objective, files))
    os.mkdir(PUBLIC)
    for case_id, objective, files in cases:
        source = os.path.join(PUBLIC, case_id, 'source')
        os.makedirs(source)
        for name in sorted(files):
            target = os.path.join(source, *name.split('/'))
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, 'wb') as handle:
                handle.write(files[name])
        with open(os.path.join(PUBLIC, case_id, 'objective.txt'), 'wb') as handle:
            handle.write((objective + '\n').encode('utf-8'))
    hashes, modes = {}, {}
    for dirpath, dirnames, filenames in os.walk(PUBLIC):
        dirnames.sort()
        for name in dirnames:
            full = os.path.join(dirpath, name)
            os.chmod(full, 0o755)
            modes[os.path.relpath(full, COHORT)] = 0o755
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            os.chmod(full, 0o644)
            rel = os.path.relpath(full, COHORT)
            modes[rel] = 0o644
            with open(full, 'rb') as handle:
                hashes[rel] = hashlib.sha256(handle.read()).hexdigest()
    os.chmod(PUBLIC, 0o755)
    manifest = {
        'version': 1,
        'cohort': 'review-cohort-3',
        'cases': [{'id': case_id, 'source': f'public/{case_id}/source',
                   'objective': f'public/{case_id}/objective.txt', 'profile': 'python-stdlib'}
                  for case_id, _, _ in cases],
        'files': dict(sorted(hashes.items())),
        'modes': dict(sorted(modes.items())),
    }
    with open(os.path.join(COHORT, 'manifest.json'), 'w', encoding='utf-8') as handle:
        json.dump(manifest, handle, indent=2, sort_keys=False)
        handle.write('\n')
    print(f'built {len(cases)} cases, {len(hashes)} files')


if __name__ == '__main__':
    main()
