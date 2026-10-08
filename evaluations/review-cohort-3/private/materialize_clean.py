"""Write the unseeded variant (source + reference + completions) of a case to a directory.

Usage: python -B materialize_clean.py <eval-dir> <case-id> <out-dir>
"""
import json, os, shutil, sys
evaluations, case_id, out = sys.argv[1:4]
here = os.path.dirname(os.path.abspath(__file__))
cohort = 'coding-b' if case_id[0] == 'b' else 'coding-c'
number = case_id[1:]
task = [t for t in sorted(os.listdir(f'{evaluations}/{cohort}/tasks')) if t.startswith(number + '-')][0]
shutil.copytree(f'{evaluations}/{cohort}/tasks/{task}/source', out)
ref = (f'{evaluations}/{cohort}/private/references/{number}.json' if cohort == 'coding-b'
       else f'{evaluations}/{cohort}/private/{number}-reference.json')
for name, text in json.load(open(ref, encoding='utf-8')).items():
    open(os.path.join(out, name), 'w', encoding='utf-8').write(text)
completions = os.path.join(here, 'completions', case_id)
if os.path.isdir(completions):
    for name in os.listdir(completions):
        shutil.copy(os.path.join(completions, name), os.path.join(out, name))
