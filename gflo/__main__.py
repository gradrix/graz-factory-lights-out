"""Command-line entry point: python3 -m gflo."""
import argparse
import json
import logging
from pathlib import Path
import subprocess
import sys
import time

from .browser import BrowserStore
from .documents import DocumentStore, decode
from .environment import EnvironmentStore
from .prepare import prepare, validate_project, infer_profile, check as check_environment
from .observe import Observer
from .web import server

from .runner import Factory
from .sandbox import DEFAULT_IMAGE, Sandbox
from .worker import ModelWorker
from .review import Reviewer


def main(argv=None):
    parser = argparse.ArgumentParser(description='Run a bounded software task using a local model.')
    parser.add_argument('--state', default='.gflo/runs', help='Durable run directory (default: .gflo/runs)')
    parser.add_argument('--config', default='.gflo/config.json', help='Local endpoint configuration')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('doctor', help='Check the local model and installed sandbox image')
    run = sub.add_parser('run', help='Snapshot and execute a task; never modify its source repository')
    run.add_argument('task')
    run.add_argument('--environment', help='Previously prepared environment ID; otherwise infer and validate a supported profile')
    run.add_argument('--environment-store', default='.gflo/environments')
    resume = sub.add_parser('resume', help='Continue an interrupted run within its original attempt budget')
    resume.add_argument('id')
    status = sub.add_parser('status', help='Read run state without contacting the model')
    status.add_argument('id', nargs='?')
    cancel = sub.add_parser('cancel', help='Request cancellation of exactly one run')
    cancel.add_argument('id')
    watch = sub.add_parser('watch', help='Poll durable state without contacting the model')
    watch.add_argument('id', nargs='?')
    watch.add_argument('--once', action='store_true')
    serve = sub.add_parser('serve', help='Read-only loopback progress page and API')
    serve.add_argument('--port', type=int, default=8787)
    environment = sub.add_parser('environment', help='Prepare and inspect approved offline environments')
    environment.add_argument('--store', default='.gflo/environments')
    actions = environment.add_subparsers(dest='environment_action', required=True)
    preparation = actions.add_parser('prepare')
    preparation.add_argument('profile', choices=['python-stdlib', 'python-api', 'node-ts'])
    preparation.add_argument('--project', help='Validate repository package declarations before acquiring dependencies')
    inspection = actions.add_parser('inspect')
    inspection.add_argument('id')
    checking = actions.add_parser('check')
    checking.add_argument('id')
    checking.add_argument('--repeat', type=int, choices=range(1, 4), default=1)
    documents = sub.add_parser('documents', help='Approved historical document evidence and saved local answers')
    documents.add_argument('--store', default='.gflo/documents')
    document_actions = documents.add_subparsers(dest='document_action', required=True)
    document_actions.add_parser('acquire').add_argument('approval', help='Controller-approved exact URL/version/question JSON')
    for action in ('inspect', 'answer', 'replay'):
        action_parser = document_actions.add_parser(action)
        action_parser.add_argument('id')
        if action == 'answer':
            action_parser.add_argument('--question', help='New controller question for this cached evidence (at most 2048 UTF-8 bytes)')
    document_actions.add_parser('cleanup', help="Explicit cleanup of this store's interrupted work")
    browser = sub.add_parser('browser', help='Supervised owned-local-application journeys')
    browser.add_argument('--store', default='.gflo/browser')
    browser_actions = browser.add_subparsers(dest='browser_action', required=True)
    browser_actions.add_parser('prepare').add_argument('archives', help='Approved offline Playwright/core archives directory')
    browser_actions.add_parser('check').add_argument('approval', help='Approved app/checks/seed/case/support JSON')
    browser_actions.add_parser('inspect').add_argument('id')
    browser_actions.add_parser('cleanup')
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        if args.command == 'browser':
            browser_store = BrowserStore(args.store)
            if args.browser_action == 'prepare':
                result = browser_store.prepare(args.archives)
            elif args.browser_action == 'inspect':
                result = browser_store.inspect(args.id)
            elif args.browser_action == 'check':
                with Path(args.approval).open('rb') as stream:
                    raw = stream.read(8193)
                if len(raw) > 8192:
                    raise ValueError('Browser approval exceeds 8 KiB')
                result = browser_store.check(decode(raw))
            else:
                browser_store.cleanup()
                result = {'cleaned': True}
            print(json.dumps(result, indent=2))
            return 1 if result.get('receipt', {}).get('outcome', {}).get('status') == 'failed' else 0
        if args.command == 'documents':
            document_store = DocumentStore(args.store)
            if args.document_action != 'answer':
                if args.document_action == 'acquire':
                    with Path(args.approval).open('rb') as stream:
                        raw = stream.read(8193)
                    if len(raw) > 8192:
                        raise ValueError('Approval file exceeds 8 KiB')
                    result = document_store.acquire(decode(raw))
                elif args.document_action == 'inspect':
                    result = document_store.resolve(args.id)
                elif args.document_action == 'replay':
                    result = document_store.replay(args.id)
                else:
                    document_store.cleanup()
                    result = {'cleaned': True}
                print(json.dumps(result, indent=2))
                return 0
        if args.command == 'environment':
            store = EnvironmentStore(args.store)
            if args.environment_action == 'prepare':
                if args.project:
                    validate_project(store, args.profile, args.project)
                prepared = prepare(store, args.profile)
                result = {'id': prepared.id, 'profile': prepared.profile, 'runtime': prepared.runtime}
            else:
                prepared = store.resolve(args.id)
                if args.environment_action == 'inspect':
                    result = json.loads((prepared.dependencies.parent / 'receipt.json').read_text())
                else:
                    result = {'id': prepared.id, 'checks': [check_environment(prepared) for _ in range(args.repeat)]}
            print(json.dumps(result, indent=2))
            return 0
        if args.command == 'serve':
            http = server(args.state, args.port)
            print(f'GFLO read-only observer: http://127.0.0.1:{http.server_port}', flush=True)
            try:
                http.serve_forever()
            finally:
                http.server_close()
            return 0
        if args.command == 'watch':
            while True:
                print(json.dumps(Observer(args.state).status(args.id), indent=2), flush=True)
                if args.once:
                    return 0
                time.sleep(2)
        if args.command == 'cancel':
            print(json.dumps(Factory(args.state, None, None).cancel(args.id), indent=2))
            return 0
        if args.command == 'status':
            factory = Factory(args.state, None, None)
            print(json.dumps(Observer(args.state).status(args.id), indent=2))
            return 0
        config_path = Path(args.config).resolve()
        if not config_path.exists():
            raise ValueError(f'Missing {config_path}. Copy config.example.json and set your local endpoint/key file.')
        config = json.loads(config_path.read_text())
        if config.get('api_key_file'):
            config['api_key_file'] = str((config_path.parent / config['api_key_file']).resolve())
        sandbox = Sandbox(config.get('image', DEFAULT_IMAGE))
        worker = ModelWorker(config, sandbox)
        if args.command == 'documents':
            print(json.dumps(document_store.answer(args.id, worker, question=args.question), indent=2))
            return 0
        if args.command == 'doctor':
            installed = subprocess.run(['docker', 'image', 'inspect', sandbox.image, '--format', '{{.Id}}'],
                                       capture_output=True, text=True, timeout=20)
            if installed.returncode:
                raise ValueError('Pinned sandbox image is not installed. Load it before running; GFLO never pulls images.')
            models = worker.request('/v1/models', timeout=10)
            if config['model'] not in [m['id'] for m in models['data']]:
                raise ValueError('Configured model is not served at this endpoint')
            result = {'ready': True, 'endpoint': worker.endpoint, 'model': config['model'],
                      'image': installed.stdout.strip()}
            try:
                result['context'] = worker.request('/props', timeout=10)['default_generation_settings']['n_ctx']
            except (RuntimeError, KeyError):
                result['context'] = 'not advertised'
            print(json.dumps(result, indent=2))
            return 0
        environment = None
        if args.command == 'run':
            store = EnvironmentStore(args.environment_store)
            requested = json.loads(Path(args.task).read_text())
            project = Path(args.task).resolve().parent / requested['repo']
            profile = requested.get('profile') or infer_profile(project)
            if args.environment:
                environment = store.resolve(args.environment)
                profile = environment.profile
            validate_project(store, profile, project)
            if environment is None:
                environment = prepare(store, profile)
        factory = Factory(args.state, worker, sandbox.verify, cleanup=sandbox.cleanup, reviewer=Reviewer(worker),
                          environment=environment, bind_environment=sandbox.bind)
        run_id = factory.create(args.task) if args.command == 'run' else args.id
        print('Run: ' + run_id, flush=True)
        print('Evidence: ' + str(factory.state / run_id), flush=True)
        result = factory.resume(run_id)
        print(json.dumps(result, indent=2))
        return 0 if result['status'] == 'accepted' else 2
    except KeyboardInterrupt:
        print('Interrupted. Use status and resume; the workspace and attempt evidence are retained.', file=sys.stderr)
        return 130
    except (ValueError, RuntimeError, OSError, subprocess.SubprocessError, KeyError) as error:
        print('GFLO: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
