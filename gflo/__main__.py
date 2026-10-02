"""Command-line entry point: python3 -m gflo."""
import argparse
import json
import logging
from pathlib import Path
import subprocess
import sys
import time

from .observe import Observer
from .web import server

from .runner import Factory
from .sandbox import DEFAULT_IMAGE, Sandbox
from .worker import ModelWorker


def main(argv=None):
    parser = argparse.ArgumentParser(description='Run a bounded software task using a local model.')
    parser.add_argument('--state', default='.gflo/runs', help='Durable run directory (default: .gflo/runs)')
    parser.add_argument('--config', default='.gflo/config.json', help='Local endpoint configuration')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('doctor', help='Check the local model and installed sandbox image')
    run = sub.add_parser('run', help='Snapshot and execute a task; never modify its source repository')
    run.add_argument('task')
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
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
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
        factory = Factory(args.state, worker, sandbox.verify, cleanup=sandbox.cleanup)
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
