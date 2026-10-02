#!/usr/bin/env python3
"""Three actual local-model tasks observed via HTTP; inject cancel and SIGKILL.

Run from repository root after examples/prepare.py DEST. Output is a compact
receipt; raw model traces stay in the chosen private state directory.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import threading
import time
import urllib.request

from gflo.runner import Factory, save
from gflo.web import server


def qualify(state, tasks, config):
    factory = Factory(state, None, None)
    http = server(state, 0)
    thread = threading.Thread(target=http.serve_forever, daemon=True); thread.start()
    reports = []
    try:
        for name, interruption in [('invoice', 'cancel'), ('inventory', 'kill'), ('log-summary', None)]:
            run = factory.create(tasks / name / 'task.json')
            started = time.monotonic()
            injected = False
            observations = []
            args = [sys.executable, '-m', 'gflo', '--state', str(state), '--config', str(config), 'resume', run]
            for cycle in range(2 if interruption else 1):
                with (state / run / f'cli-{cycle}.log').open('w') as log:
                    process = subprocess.Popen(args, stdout=log, stderr=subprocess.STDOUT)
                    try:
                        deadline = time.monotonic() + 1800
                        while process.poll() is None:
                            if time.monotonic() > deadline:
                                raise TimeoutError('Qualification run exceeded 30 minutes')
                            with urllib.request.urlopen(f'http://127.0.0.1:{http.server_port}/api/runs/{run}', timeout=10) as response:
                                snapshot = json.load(response)
                            observation = {key: snapshot.get(key) for key in ('status', 'phase', 'owner_alive', 'heartbeat_age_s', 'attempts')}
                            if not observations or observations[-1] != observation:
                                observations.append(observation)
                            if interruption and not injected and snapshot['phase'] == 'model_wait':
                                if interruption == 'cancel':
                                    factory.cancel(run)
                                else:
                                    process.kill()
                                injected = True
                            time.sleep(1)
                        process.wait(timeout=45)
                    finally:
                        if process.poll() is None:
                            process.kill(); process.wait()
                if cycle == 0 and interruption:
                    with urllib.request.urlopen(f'http://127.0.0.1:{http.server_port}/api/runs/{run}') as response:
                        stopped = json.load(response)
                    assert stopped['status'] == ('cancelled' if interruption == 'cancel' else 'interrupted'), stopped
                    assert injected
            with urllib.request.urlopen(f'http://127.0.0.1:{http.server_port}/api/runs/{run}') as response:
                result = json.load(response)
            with urllib.request.urlopen(f'http://127.0.0.1:{http.server_port}/api/runs/{run}/events') as response:
                events = json.load(response)
            report = {'task': name, 'run': run, 'injection': interruption, 'injected': injected,
                      'status': result['status'], 'attempts': result['attempts'],
                      'elapsed_s': round(time.monotonic()-started, 1), 'event_count': len(events),
                      'accepted_events': sum(e['kind'] == 'accepted' for e in events),
                      'phases_observed': sorted(set(o['phase'] for o in observations)),
                      'polls': len(observations)}
            reports.append(report)
            save(state / 'qualification.json', reports)
            print(json.dumps(report), flush=True)
            assert result['status'] == 'accepted', report
            assert report['accepted_events'] == 1, report
    finally:
        http.shutdown(); http.server_close(); thread.join()
    return reports


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--tasks', type=Path, required=True)
    parser.add_argument('--config', type=Path, default=Path('.gflo/config.json'))
    args = parser.parse_args()
    qualify(args.state.resolve(), args.tasks.resolve(), args.config.resolve())
