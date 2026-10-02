#!/usr/bin/env python3
"""Private known-case paired repair probe. Default prepares only; --execute calls model."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

sys.path.insert(0, str(Path.cwd()))
from gflo.runner import Factory, fingerprint
from gflo.sandbox import Sandbox
from gflo.worker import ModelWorker
from gflo.review import Reviewer

IMAGE = 'sha256:fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc'
CASES = [('03-bit-fields', '43b7647311b0', ('none', 'thinking1024')),
         ('06-failed-candidate', 'fbb865b3744f', ('thinking1024', 'none'))]


class ProbeWorker(ModelWorker):
    def __init__(self, config, sandbox, request_receipts, thinking=False):
        super().__init__(config, sandbox)
        self.request_receipts = request_receipts
        self.thinking = thinking

    def request(self, path, body=None, timeout=300):
        if not (body and body.get('tools')):
            return super().request(path, body, timeout)
        effective = copy.deepcopy(body)
        if self.thinking:
            effective['reasoning_effort'] = 'medium'
            effective['thinking_budget_tokens'] = 1024
            effective['chat_template_kwargs'] = dict(effective.get('chat_template_kwargs', {}),
                enable_thinking=True)
        assert effective.get('max_tokens') == 4096
        # Match ModelWorker.request's actual JSON serialization without retaining contents.
        serialized = json.dumps(effective).encode()
        record = {'sequence': len(self.request_receipts) + 1,
                  'request_sha256': hashlib.sha256(serialized).hexdigest(),
                  'request_bytes': len(serialized),
                  'effective_profile': {key: effective.get(key) for key in
                    ('model', 'max_tokens', 'temperature', 'reasoning_effort', 'thinking_budget_tokens', 'chat_template_kwargs')},
                  'timeout_seconds': timeout}
        self.request_receipts.append(record)
        started = time.monotonic()
        try:
            response = super().request(path, effective, timeout)
            record['usage'] = response.get('usage')
            record['finish_reasons'] = [choice.get('finish_reason') for choice in response.get('choices', [])]
            return response
        except BaseException as error:
            record['error_type'] = type(error).__name__
            raise
        finally:
            record['elapsed_seconds'] = round(time.monotonic() - started, 3)


def save(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, indent=2) + '\n')
    temp.replace(path)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], check=True,
                          capture_output=True, text=True, timeout=30).stdout.strip()


def copy_regular(source, destination):
    destination.mkdir(parents=True)
    for path in sorted(source.rglob('*')):
        if path.is_symlink() or not (path.is_dir() or path.is_file()):
            raise ValueError('Unsupported frozen source entry')
        target = destination / path.relative_to(source)
        if path.is_dir():
            target.mkdir(exist_ok=True)
        else:
            shutil.copyfile(path, target)
            target.chmod(path.stat().st_mode & 0o777)


class ProbeDeadline(BaseException):
    pass


def deadline(_signum, _frame):
    # Avoid worker tool/error handlers swallowing the whole-arm deadline.
    raise ProbeDeadline('Paired repair arm exceeded 900 seconds')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-state', type=Path,
                        default=Path('/home/gradrix/gflo-runtime/.gflo/stage2-coding-c'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--config', type=Path)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    os.umask(0o077)
    out = args.output.resolve()
    # Refuse reuse: every invocation has fresh sources/state and cannot overwrite evidence.
    out.mkdir(parents=True, exist_ok=False)
    os.chmod(out, 0o700)
    receipt = {'kind': 'known-case paired repair prototype; not unseen qualification',
               'image': IMAGE, 'order': [], 'arms': [],
               'budgets': {'attempts': 1, 'turns': 24, 'wall_seconds': 900,
                           'total_tokens_per_coder_response': 4096, 'thinking_tokens': 1024},
               'initial_failure_evidence': 'omitted consistently in both arms; failed files retained',
               'reviewer': 'unchanged Reviewer: medium, enable_thinking true, top-level thinking_budget_tokens 1024, max_tokens 4096',
               'executed': False}
    frozen = []
    for case, source_id, arms in CASES:
        original = args.source_state.resolve() / source_id
        task = json.loads((original / 'task.json').read_text())
        source_hash = fingerprint(original / 'workspace')
        acceptance_hash = fingerprint(original / 'acceptance')
        if acceptance_hash != task['acceptance_hash']:
            raise ValueError('Original acceptance fingerprint changed')
        for arm in arms:
            label = case + '-' + arm
            area = out / label
            area.mkdir()
            source, acceptance = area / 'source', area / 'acceptance'
            copy_regular(original / 'workspace', source)
            copy_regular(original / 'acceptance', acceptance)
            if fingerprint(source) != source_hash or fingerprint(acceptance) != acceptance_hash:
                raise ValueError('Frozen copy differs from original')
            git(source, 'init', '-q')
            git(source, 'add', '-f', '.')
            git(source, '-c', 'user.name=GFLO probe', '-c', 'user.email=probe@localhost',
                'commit', '-q', '-m', 'Frozen terminal candidate for paired repair')
            assert git(source, 'status', '--porcelain') == ''
            new_task = {'repo': 'source', 'acceptance': 'acceptance',
                        'objective': task['objective'], 'checks': task['checks'],
                        'max_attempts': 1, 'max_turns': 24,
                        'wall_time_seconds': 900, 'review_required': True}
            save(area / 'task.json', new_task)
            record = {'label': label, 'arm': arm, 'source_run_id': source_id,
                      'initial_source_hash': source_hash, 'acceptance_hash': acceptance_hash,
                      'objective_sha256': digest(task['objective']), 'checks_sha256': digest(task['checks']),
                      'source_commit': git(source, 'rev-parse', 'HEAD'), 'status': 'prepared'}
            receipt['order'].append(label)
            receipt['arms'].append(record)
        frozen.append((original, source_hash, acceptance_hash))
    save(out / 'receipt.json', receipt)
    if not args.execute:
        print(json.dumps({'prepared': str(out), 'model_calls': 0, 'arms': receipt['order']}))
        return
    if args.config is None:
        raise ValueError('--execute requires private --config')
    config_path = args.config.resolve()
    config = json.loads(config_path.read_text())
    if config.get('api_key_file'):
        config['api_key_file'] = str((config_path.parent / config['api_key_file']).resolve())
    config.update(image=IMAGE, reasoning='none')
    # Image readback and runtime check are independent of model assertions.
    inspected = subprocess.run(['docker', 'image', 'inspect', IMAGE], check=True,
                               capture_output=True, text=True, timeout=20)
    image = json.loads(inspected.stdout)[0]
    if image['Id'] != IMAGE:
        raise ValueError('Unexpected image identity')
    sandbox = Sandbox(IMAGE)
    runtime_dir = out / 'runtime-check'
    runtime_dir.mkdir()
    runtime = sandbox.execute(runtime_dir, ['python', '-c',
        'import json,sys;print(json.dumps({"version":sys.version,"executable":sys.executable}));assert sys.version_info[:3]==(3,12,13)'])
    if runtime['exit_code'] != 0:
        raise ValueError('Target Python runtime mismatch')
    receipt['runtime'] = runtime
    receipt['image_inspect'] = {'id': image['Id'], 'repo_digests': image['RepoDigests'],
                                'os': image['Os'], 'architecture': image['Architecture']}
    receipt['executed'] = True
    old_handler = signal.signal(signal.SIGALRM, deadline)
    try:
        for record in receipt['arms']:
            area = out / record['label']
            sandbox = Sandbox(IMAGE)
            record['coder_requests'] = []
            coder = ProbeWorker(config, sandbox, record['coder_requests'],
                                thinking=record['arm'] == 'thinking1024')
            reviewer_client = ModelWorker(config, sandbox)
            factory = Factory(area / 'state', coder, sandbox.verify,
                              cleanup=sandbox.cleanup, reviewer=Reviewer(reviewer_client))
            run_id = factory.create(area / 'task.json')
            record['run_id'] = run_id
            record['status'] = 'running'
            print(json.dumps({'event': 'arm_started', 'label': record['label'], 'run_id': run_id}), flush=True)
            save(out / 'receipt.json', receipt)
            started = time.monotonic()
            signal.setitimer(signal.ITIMER_REAL, 900)
            try:
                result = factory.resume(run_id)
                record['status'] = result['status']
                record['attempts'] = result['attempts']
            except (Exception, ProbeDeadline) as error:
                # Raw HTTP/config error contents remain private; compact receipts omit them.
                record['status'] = 'failed'
                record['error_type'] = type(error).__name__
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
                record['elapsed_seconds'] = round(time.monotonic() - started, 3)
                try:
                    sandbox.cleanup(area / 'state' / run_id / 'workspace')
                except Exception:
                    record['cleanup_failed'] = True
                factory.db.close()
            attempt = area / 'state' / run_id / 'attempts' / '1'
            for filename in ('verification.json', 'review.json', 'worker.json'):
                path = attempt / filename
                if path.exists():
                    record[filename + '_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
            verification = attempt / 'verification.json'
            if verification.exists():
                value = json.loads(verification.read_text())
                record['acceptance_passed'] = all(x.get('exit_code') == 0 for x in value.get('checks', [])) if value.get('checks') else None
            review_path = attempt / 'review.json'
            if review_path.exists():
                record['review_decision'] = json.loads(review_path.read_text()).get('decision')
            save(out / 'receipt.json', receipt)
            print(json.dumps({'event': 'arm_finished', 'label': record['label'],
                              'status': record['status'], 'elapsed_seconds': record['elapsed_seconds'],
                              'acceptance_passed': record.get('acceptance_passed'),
                              'review_decision': record.get('review_decision'),
                              'coder_requests': len(record['coder_requests'])}), flush=True)
            if record.get('cleanup_failed'):
                raise RuntimeError('Cleanup failed; refusing next arm')
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_handler)
        for original, source_hash, acceptance_hash in frozen:
            if fingerprint(original / 'workspace') != source_hash or fingerprint(original / 'acceptance') != acceptance_hash:
                raise RuntimeError('Original frozen cohort changed during experiment')
        save(out / 'receipt.json', receipt)
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
