#!/usr/bin/env python3
"""Root-operated rig trial. No inference unless explicitly invoked with --run."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_json(path):
    return json.loads(Path(path).read_text())


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--candidate-sha256', required=True)
    p.add_argument('--contract', type=Path, required=True)
    p.add_argument('--contract-sha256', required=True)
    p.add_argument('--config', type=Path, required=True, help='Existing private rig config; contents never emitted')
    p.add_argument('--serving-container', required=True)
    p.add_argument('--expected-serving-id', required=True)
    p.add_argument('--expected-serving-image', required=True)
    p.add_argument('--output', type=Path, required=True, help='New directory; refuses existing output/store')
    p.add_argument('--run', action='store_true', help='Authorize exactly two answer attempts; no automatic retries')
    args = p.parse_args()
    if not args.run:
        p.error('No action taken: explicit --run is required; this script makes live local-model calls')
    repo = args.repo.resolve()
    if args.output.exists():
        p.error('Output already exists; preserve it and choose a new directory')
    args.output.mkdir(parents=True, mode=0o700)
    out = args.output.resolve()
    receipt = {'status': 'started', 'candidate_manifest': args.candidate_sha256,
               'contract_sha256': args.contract_sha256, 'questions': [], 'model_calls_authorized': 2,
               'semantic_verdict': 'independent review required'}

    def save():
        (out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')

    def candidate():
        assert sha(args.candidate.read_bytes()) == args.candidate_sha256, 'Candidate manifest changed'
        mapping = file_json(args.candidate)
        for name, digest in mapping['files'].items():
            path = repo / name
            assert path.resolve().is_relative_to(repo), 'Candidate path escapes repo'
            assert sha(path.read_bytes()) == digest, 'Candidate file changed: ' + name
        assert sha(args.contract.read_bytes()) == args.contract_sha256, 'Trial contract changed'
        return mapping

    def serving():
        value = json.loads(subprocess.check_output(['docker', 'inspect', args.serving_container], timeout=15))[0]
        assert value['Id'] == args.expected_serving_id and value['Image'] == args.expected_serving_image, 'Serving identity mismatch'
        assert value['State']['Running'], 'Serving container stopped'
        command = value['Config']['Cmd']
        def option(*names):
            for name in names:
                if name in command:
                    return command[command.index(name) + 1]
                for item in command:
                    if name.startswith('--') and item.startswith(name + '='):
                        return item[len(name) + 1:]
                    if name.startswith('-') and not name.startswith('--') and item.startswith(name) and len(item) > len(name):
                        return item[len(name):]
            raise AssertionError('Required serving option missing: ' + names[0])
        assert int(option('-c', '--ctx-size')) == contract['profile']['context'], 'Context mismatch'
        assert option('--cache-type-k') == option('--cache-type-v') == contract['profile']['cache'], 'KV cache mismatch'
        assert option('--alias') == contract['profile']['model'], 'Model alias mismatch'
        # Persist only selected nonsecret identity fields, never full config/env/command.
        return {'id': value['Id'], 'image': value['Image'], 'model_file': option('--model', '-m'),
                'alias': option('--alias'), 'context': int(option('-c', '--ctx-size')),
                'cache_k': option('--cache-type-k'), 'cache_v': option('--cache-type-v'),
                'parallel': int(option('-np', '--parallel')),
                'command_sha256': sha(json.dumps(command, separators=(',', ':')).encode())}

    save()
    started = time.monotonic()
    try:
        candidate()
        contract = file_json(args.contract)
        assert len(contract['questions']) == 2, 'This harness is bounded to the frozen two-question trial'
        assert contract['profile']['max_output_tokens'] == 2048 and contract['profile']['request_timeout_s'] == 120
        assert contract['profile']['reasoning'] == 'medium'
        receipt['serving_before'] = serving()
        sys.path.insert(0, str(repo))
        from gflo.documents import DocumentStore
        from gflo.worker import ModelWorker
        from gflo.sandbox import DEFAULT_IMAGE
        from gflo.guard import run
        config = file_json(args.config)
        assert config['model'] == contract['profile']['model'], 'Configured model mismatch'
        if config.get('api_key_file'):
            config['api_key_file'] = str((args.config.resolve().parent / config['api_key_file']).resolve())
        class RecordingWorker(ModelWorker):
            answer_name = None
            def request(self, path, body=None, timeout=300, *, max_response_bytes=None):
                if path != '/v1/chat/completions':
                    return super().request(path, body, timeout, max_response_bytes=max_response_bytes)
                assert self.answer_name is not None and max_response_bytes == 65536 and timeout == 120
                from gflo.documents import encoded
                prefix = out / self.answer_name
                request_record = {'request_sha256': sha(encoded(body)), 'timeout_s': timeout,
                                  'max_response_bytes': max_response_bytes, 'tools_present': 'tools' in body,
                                  'max_tokens': body.get('max_tokens'), 'reasoning_effort': body.get('reasoning_effort'),
                                  'thinking_budget_tokens': body.get('thinking_budget_tokens')}
                prefix.with_name(prefix.name + '-request.json').write_text(json.dumps(request_record, indent=2) + '\n')
                response = super().request(path, body, timeout, max_response_bytes=max_response_bytes)
                raw = json.dumps(response, ensure_ascii=False, separators=(',', ':')).encode()
                if len(raw) <= max_response_bytes:
                    prefix.with_name(prefix.name + '-response.json').write_bytes(raw)
                else:
                    prefix.with_name(prefix.name + '-response-prefix.bin').write_bytes(raw[:max_response_bytes])
                    prefix.with_name(prefix.name + '-response-truncation.json').write_text(json.dumps(
                        {'decoded_response_bytes': len(raw), 'prefix_bytes': max_response_bytes, 'complete_sha256': sha(raw)}))
                return response
        client = RecordingWorker(config, None)
        models = client.request('/v1/models', timeout=10, max_response_bytes=65536)
        assert config['model'] in [m['id'] for m in models['data']], 'Endpoint alias not served'
        props = client.request('/props', timeout=10, max_response_bytes=65536)
        assert props['default_generation_settings']['n_ctx'] == contract['profile']['context'], 'Endpoint context mismatch'
        receipt['endpoint_model_before'] = {'alias': config['model'], 'context': props['default_generation_settings']['n_ctx']}
        store = DocumentStore(out / 'store')
        evidence = store.acquire({'url': contract['url'], 'source_version': contract['source_version'],
                                  'question': contract['questions'][0]['question']})
        (out / 'evidence.json').write_text(json.dumps(evidence, indent=2) + '\n')
        receipt['evidence_id'] = evidence['id']; save()
        for question in contract['questions']:
            candidate(); assert serving() == receipt['serving_before'], 'Serving changed before answer'
            row = {'name': question['name'], 'expected_status': question['expected_status'], 'attempts': 1}
            receipt['questions'].append(row); save()
            assert question['name'].replace('_', '').isalnum(), 'Unsafe question artifact name'
            client.answer_name = question['name']
            then = time.monotonic()
            try:
                answer = store.answer(evidence['id'], client, question=question['question'])
                (out / (question['name'] + '-answer.json')).write_text(json.dumps(answer, indent=2) + '\n')
                row.update(answer_id=answer['id'], status=answer['answer']['status'])
                expected = 'insufficient_evidence' if question['expected_status'] == 'insufficient' else question['expected_status']
                row['expected_status_matches'] = row['status'] == expected
            except Exception as error:
                from gflo.observe import redact
                row['error'] = redact(str(error))[:2048]
            row['response_evidence'] = [p.name for p in out.glob(question['name'] + '-response*')]
            row['request_evidence'] = question['name'] + '-request.json'
            row['elapsed_s'] = time.monotonic() - then; save()
        def record_hashes():
            return {str(p.relative_to(store.root)): sha(p.read_bytes()) for p in sorted(store.root.rglob('*'))
                    if p.is_file() and p.name != '.lock'}
        before = record_hashes()
        replay_ids = [row['answer_id'] for row in receipt['questions'] if 'answer_id' in row]
        code = ('import json,platform;from gflo.documents import DocumentStore;'
                's=DocumentStore("/store");print(json.dumps({"python":platform.python_version(),'
                '"answers":[s.replay(i) for i in ' + repr(replay_ids) + ']}))')
        name = 'gflo-document-replay-' + uuid.uuid4().hex[:16]
        cmd = ['docker', 'run', '--rm', '--pull', 'never', '--name', name, '--runtime', 'runc',
               '--network', 'none', '--read-only', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
               '--user', f'{os.getuid()}:{os.getgid()}', '--memory', '256m', '--memory-swap', '256m',
               '--cpus', '1', '--pids-limit', '64', '--shm-size', '8m',
               '--tmpfs', '/tmp:rw,nosuid,nodev,size=16m,mode=1777', '--env', 'HOME=/tmp',
               '--env', 'PYTHONDONTWRITEBYTECODE=1', '--env', 'PYTHONPATH=/app', '--workdir', '/tmp',
               '--mount', f'type=bind,src={repo}/gflo,dst=/app/gflo,readonly',
               '--mount', f'type=bind,src={store.root},dst=/store', DEFAULT_IMAGE, 'python', '-B', '-c', code]
        captured = io.BytesIO()
        result = run(cmd, name, 20, output=captured, max_output_bytes=262144, inspect_path=out / 'replay-executor.json')
        (out / 'replay-execution.json').write_text(json.dumps(result, indent=2) + '\n')
        assert result['exit_code'] == 0, 'Offline replay failed'
        replay = json.loads(captured.getvalue()); (out / 'offline-replay.json').write_text(json.dumps(replay, indent=2) + '\n')
        assert replay['python'] == '3.12.13', 'Replay runtime mismatch'
        assert before == record_hashes(), 'Replay changed stored records'
        assert len(replay['answers']) == len(replay_ids), 'Replay omitted answers'
        for row, actual in zip([r for r in receipt['questions'] if 'answer_id' in r], replay['answers']):
            expected = file_json(out / (row['name'] + '-answer.json'))
            assert {k:v for k,v in actual.items() if k != 'age_seconds'} == {k:v for k,v in expected.items() if k != 'age_seconds'}, 'Replay changed answer/provenance'
        receipt['offline_replay'] = {'passed': True, 'answers': len(replay_ids), 'record_hashes': before,
                                     'network': 'none', 'config_or_key_mounts': False}
        candidate(); receipt['serving_after'] = serving()
        assert receipt['serving_after'] == receipt['serving_before'], 'Serving changed during trial'
        models = client.request('/v1/models', timeout=10, max_response_bytes=65536)
        props = client.request('/props', timeout=10, max_response_bytes=65536)
        assert config['model'] in [m['id'] for m in models['data']] and props['default_generation_settings']['n_ctx'] == contract['profile']['context']
        receipt['status'] = 'structural_pass_semantic_pending' if all(r.get('expected_status_matches') for r in receipt['questions']) else 'failed'
    except Exception as error:
        # No private configuration or raw provider body is published here.
        receipt['status'] = 'failed'
        receipt['failure_type'] = type(error).__name__
        receipt['failure'] = str(error)[:2048] if isinstance(error, AssertionError) else 'Operation failed; inspect bounded per-operation evidence.'
    finally:
        try: candidate(); receipt['candidate_after_matches'] = True
        except Exception: receipt['candidate_after_matches'] = False; receipt['status'] = 'failed'
        if 'serving_before' in receipt:
            try:
                receipt['serving_after'] = serving()
                if receipt['serving_after'] != receipt['serving_before']:receipt['status'] = 'failed'
            except Exception:receipt['serving_after_error'] = True; receipt['status'] = 'failed'
        receipt['elapsed_s'] = time.monotonic() - started; save()
    print(json.dumps({'status': receipt['status'], 'receipt': str(out / 'receipt.json'),
                      'answers': [{'name': q['name'], 'id': q.get('answer_id'), 'status': q.get('status'),
                                   'expected_status_matches': q.get('expected_status_matches')} for q in receipt['questions']]}, indent=2))
    return 0 if receipt['status'] == 'structural_pass_semantic_pending' else 1


if __name__ == '__main__':
    raise SystemExit(main())
