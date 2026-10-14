"""Model gate: rerun the recorded end-to-end measurements on the served model and compare them with the gates (rig).

  gate.py run BENCH OUT --config CONFIG [--suites small,features,tests] [--smoke]
  gate.py report OUT

BENCH is the private benchmark directory (manifest.json, tasks, hidden tests, environments; docs/model-upgrade.md).
Suites: small (16 single-commit changes, default worker and reviewer), features (6 commit chains as one task each),
tests (test factory overnight on 3 large modules). `--smoke` runs one small task into OUT/smoke to check the pipeline.
OUT is resumable: rerun the same command after an interruption, and finished tasks are kept. One OUT belongs to one
model: `run` refuses an OUT recorded for different weights. `report` writes OUT/summary.json and OUT/report.md
against ops/benchmark/gates.json and prints them.
"""
import argparse
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import urllib.request

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
GATES = HERE / 'gates.json'
PROFILE = Path.home() / '.local/state/gflo-model/profile.json'
SUITES = ('small', 'features', 'tests')


def served_model(config):
    """What the endpoint serves now: its model id plus the weights ops/model.py last started, when recorded."""
    config = json.loads(Path(config).read_text())
    key = Path(config['api_key_file']).expanduser().read_text().strip()
    request = urllib.request.Request(config['endpoint'].rstrip('/') + '/v1/models', headers={'Authorization': 'Bearer ' + key})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request, timeout=10) as response:
        model = {'id': json.load(response)['data'][0]['id']}
    if PROFILE.exists():
        profile = json.loads(PROFILE.read_text())
        model.update({name: profile.get(name) for name in ('weights', 'runtime', 'context', 'cache')})
    return model


def claim(out, model):
    """Record OUT's model, or refuse when OUT already holds results for another one."""
    out.mkdir(parents=True, exist_ok=True)
    path = out / 'model.json'
    if path.exists():
        recorded = json.loads(path.read_text())
        if (recorded.get('weights') or recorded['id']) != (model.get('weights') or model['id']):
            raise SystemExit(f'{out} holds results for {recorded}; use a new OUT for {model}')
        return
    code = os.environ.get('GFLO_CODE')
    if not code:
        found = subprocess.run(['git', '-C', str(REPO), 'rev-parse', '--short', 'HEAD'], capture_output=True, text=True)
        code = found.stdout.strip() or 'unknown'
    path.write_text(json.dumps(dict(model, code=code), indent=1) + '\n')


def drive(bench, group, out, config, commits, arm, steps=None):
    command = [sys.executable, str(REPO / 'ops/delivery/drive.py'), str(bench / group['tasks']), str(bench / group['mined']),
               str(bench / 'envs'), str(out / 'runs'), str(config), str(out / 'results.jsonl'),
               '--commits', ','.join(commits), '--arms', arm]
    if steps:
        command += ['--steps', str(bench / steps)]
    subprocess.run(command, check=True, cwd=REPO)


def run(bench, out, config, suites, smoke=False):
    bench, out, config = Path(bench).resolve(), Path(out).resolve(), Path(config).resolve()
    manifest = json.loads((bench / 'manifest.json').read_text())
    claim(out, served_model(config))
    if smoke:
        spec = manifest['smoke']
        group = next(g for g in manifest[spec['suite']] if spec['commit'] in g['commits'])
        drive(bench, group, out / 'smoke', config, [spec['commit']], 'single')
        return
    if 'small' in suites:
        for group in manifest['small']:
            drive(bench, group, out / 'small', config, group['commits'], 'single')
    if 'features' in suites:
        for group in manifest['features']:  # direct arm: one task with the combined objective (decision 014)
            drive(bench, group, out / 'features', config, group['commits'], 'single')
    if 'tests' in suites:
        spec = manifest['tests']
        command = [sys.executable, '-m', 'gflo', '--state', str(out / 'tests' / 'runs'), '--config', str(config),
                   'tests', 'overnight', str(bench / spec['repo']), '--out', str(out / 'tests' / 'queue'),
                   '--limit', str(spec['limit']), '--hours', str(spec['hours']), '--environment-store', str(bench / 'envs')]
        for prefix in spec.get('include', []):
            command += ['--include', prefix]
        for pair in spec.get('env', []):
            command += ['--env', pair]
        (out / 'tests').mkdir(parents=True, exist_ok=True)
        with (out / 'tests' / 'overnight.log').open('a') as log:
            subprocess.run(command, check=True, cwd=REPO, stdout=log, stderr=subprocess.STDOUT)


def rows(path):
    if not path.exists():
        return []
    latest = {}
    for row in map(json.loads, path.read_text().splitlines()):
        latest[(row['commit'], row['arm'])] = row  # a resumed task's last row counts
    return list(latest.values())


def summarize(out):
    out = Path(out)
    summary = {}
    for suite in ('small', 'features', 'smoke'):
        found = rows(out / suite / 'results.jsonl')
        if found:
            times = [row['elapsed_s'] for row in found if isinstance(row.get('elapsed_s'), (int, float))]
            summary[suite] = {'delivered': sum(bool(row.get('delivered')) for row in found),
                              'false_accepts': sum(bool(row.get('false_accept')) for row in found),
                              'of': len(found), 'unscored': sum(not row.get('scored') for row in found),
                              'median_s': round(statistics.median(times)) if times else None,
                              'tasks': {row['commit']: ('delivered' if row.get('delivered') else 'false accept'
                                                        if row.get('false_accept') else row.get('factory_status') or 'error')
                                        for row in found}}
    queue = out / 'tests' / 'queue' / 'queue.json'
    if queue.exists():
        done = json.loads(queue.read_text())['done']
        summary['tests'] = {'accepted': sum(value.get('status') == 'accepted' for value in done.values()), 'of': len(done),
                            'modules': {target: value.get('status') for target, value in done.items()}}
    return summary


def verdicts(summary, gates, expected):
    """pass / fail / borderline (repeat the suite once) / incomplete per gate."""
    results = []
    for gate in gates['gates']:
        found = summary.get(gate['suite'])
        if not found or found['of'] < expected[gate['suite']] or found.get('unscored'):
            verdict = 'incomplete'
        elif 'min_accepted' in gate:
            accepted = found['accepted']
            verdict = 'pass' if accepted >= gate['min_accepted'] else 'borderline' if accepted == gate['min_accepted'] - 1 else 'fail'
        else:
            short = gate['min_delivered'] - found['delivered']
            over = found['false_accepts'] - gate['max_false_accepts']
            verdict = 'pass' if short <= 0 and over <= 0 else 'borderline' if short <= 1 and over <= 1 else 'fail'
        results.append(dict(gate, verdict=verdict))
    return results


def show(result):
    if 'accepted' in result:
        return f"{result['accepted']}/{result['of']} accepted"
    return f"{result['delivered']}/{result['of']} delivered, {result['false_accepts']} false accepts"


def report(out):
    out = Path(out)
    gates = json.loads(GATES.read_text())
    summary = summarize(out)
    results = verdicts(summary, gates, {suite: gates['baseline'][suite]['of'] for suite in SUITES})
    model = json.loads((out / 'model.json').read_text()) if (out / 'model.json').exists() else {}
    (out / 'summary.json').write_text(json.dumps({'model': model, 'summary': summary, 'gates': results}, indent=1) + '\n')
    lines = [f"# Model gate: {model.get('weights') or model.get('id')}", '', f"Code {model.get('code')}, context {model.get('context')}.", '',
             '| suite | this model | baseline |', '|---|---|---|']
    for suite in SUITES:
        now = summary.get(suite)
        median = f" (median {now['median_s']} s)" if now and now.get('median_s') else ''
        lines.append(f"| {suite} | {show(now) if now else 'not run'}{median} | {show(gates['baseline'][suite])} |")
    lines += ['', '| gate | verdict | opens |', '|---|---|---|']
    lines += [f"| {r['id']} | **{r['verdict']}** | {r['opens']} |" for r in results]
    lines += ['', 'Borderline: repeat that suite once into a new OUT before deciding. Next steps: docs/model-upgrade.md.', '']
    (out / 'report.md').write_text('\n'.join(lines))
    print('\n'.join(lines))
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='action', required=True)
    run_parser = sub.add_parser('run')
    run_parser.add_argument('bench')
    run_parser.add_argument('out')
    run_parser.add_argument('--config', required=True)
    run_parser.add_argument('--suites', default=','.join(SUITES))
    run_parser.add_argument('--smoke', action='store_true')
    report_parser = sub.add_parser('report')
    report_parser.add_argument('out')
    args = parser.parse_args()
    if args.action == 'run':
        unknown = set(args.suites.split(',')) - set(SUITES)
        if unknown:
            parser.error('unknown suites: ' + ', '.join(sorted(unknown)))
        run(args.bench, args.out, args.config, args.suites.split(','), args.smoke)
        report(args.out)
    else:
        report(args.out)
