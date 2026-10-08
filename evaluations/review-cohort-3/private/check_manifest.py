import hashlib, json, os, stat, sys
cohort = sys.argv[1]
m = json.load(open(os.path.join(cohort, 'manifest.json')))
files, modes = {}, {}
for dirpath, dirnames, filenames in os.walk(os.path.join(cohort, 'public')):
    for d in dirnames:
        p = os.path.join(dirpath, d); modes[os.path.relpath(p, cohort)] = stat.S_IMODE(os.lstat(p).st_mode)
    for f in filenames:
        p = os.path.join(dirpath, f); r = os.path.relpath(p, cohort)
        modes[r] = stat.S_IMODE(os.lstat(p).st_mode)
        files[r] = hashlib.sha256(open(p, 'rb').read()).hexdigest()
ids = [c['id'] for c in m['cases']]
ok = (files == m['files'] and modes == m['modes'] and ids == sorted(ids) and len(ids) == 24
      and set(modes.values()) == {0o644, 0o755})
print('manifest files/modes match disk:', ok, '| files', len(files), '| entries', len(modes))
sys.exit(0 if ok else 1)
