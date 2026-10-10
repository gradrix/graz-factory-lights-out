"""Run one command in a workspace inside a prepared, offline gflo environment (rig helper).

usage: env_exec.py STORE ENV_ID WORKSPACE [--timeout S] [--readonly] -- COMMAND...
Prints the sandbox result as JSON; exit code mirrors the command.
"""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from gflo.environment import EnvironmentStore  # noqa: E402
from gflo.sandbox import Sandbox  # noqa: E402


def execute(store, environment, workspace, command, *, timeout=600, readonly=False):
    sandbox = Sandbox()
    sandbox.bind(EnvironmentStore(store).resolve(environment))
    try:
        return sandbox.execute(workspace, command, timeout=timeout, readonly=readonly)
    finally:
        sandbox.cleanup(workspace)


if __name__ == '__main__':
    if '--' not in sys.argv:
        raise SystemExit(__doc__)
    split = sys.argv.index('--')
    parser = argparse.ArgumentParser()
    parser.add_argument('store')
    parser.add_argument('environment')
    parser.add_argument('workspace')
    parser.add_argument('--timeout', type=int, default=600)
    parser.add_argument('--readonly', action='store_true')
    args = parser.parse_args(sys.argv[1:split])
    result = execute(args.store, args.environment, args.workspace, sys.argv[split + 1:], timeout=args.timeout, readonly=args.readonly)
    print(json.dumps(result))
    sys.exit(result['exit_code'] or 0)
