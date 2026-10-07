#!/usr/bin/env python3
"""Per-requirement saved-evidence review units; never executes candidate commands."""
import argparse
import json
from pathlib import Path
import signal
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from executable_review_prototype import PROFILE, REQUEST_BYTES, RESPONSE_BYTES, ReviewClient
from review_evidence_prototype import (CAPACITY, SYSTEM as EVIDENCE_SYSTEM, create_ledger, read_file,
                                       render, validate_diagnosis, verify_packages)
from planning_pilot_prototype import (CaptureOpener, digest, encoded, journal, pilot_lease, publish_result,
                                      supervise, wait_idle)
from gflo.runner import save
from gflo.observe import redact

MAX_UNITS = 32
UNIT_SECONDS = 300
HTTP_SECONDS = 240
REASONING_BUDGET = 4096
MAX_TOKENS = 8192
METER_BYTES = 4 * 1024 * 1024
SYSTEM = EVIDENCE_SYSTEM + (' Assignment: judge only the single objective line named in the final ASSIGNMENT. '
    'Every finding must include that line number in requirements. pass means the captured evidence and source show '
    'no blocking violation of that line; repair means a blocking violation of that line with cited observations. '
    'Ignore other requirements; they are judged separately.')


class UnitClient(ReviewClient):
    """The qualified durable one-use final path with the contract-2 thinking cap."""
    def __init__(self, config, ledger, transport=None):
        if ledger.read()['phase'] != 'final': raise ValueError('Final phase required')
        super().__init__(config, ledger, transport)

    def complete(self, messages):
        if self.ledger.read()['phase'] != 'final': raise ValueError('Request phase differs from durable ledger')
        body = {**PROFILE, 'thinking_budget_tokens': REASONING_BUDGET, 'max_tokens': MAX_TOKENS,
                'messages': messages, 'response_format': {'type': 'json_object'}}
        raw = encoded(body)
        if len(raw) > REQUEST_BYTES: raise ValueError('Request capacity before transport')
        number = self.ledger.reserve('requests', {'request_sha256': digest(raw), 'role': 'unit-reviewer'})
        target = self.ledger.root / 'requests' / f'{number:02d}'; target.mkdir(parents=True)
        (target / 'request.json').write_bytes(raw)
        original = getattr(self.transport, 'opener', None)
        if original is not None: self.transport.opener = CaptureOpener(original, target)
        started = time.monotonic()
        try:
            response = self.transport.request('/v1/chat/completions', body, timeout=min(HTTP_SECONDS, self.ledger.seconds()),
                                              max_response_bytes=RESPONSE_BYTES)
            raw = encoded(response)
            if len(raw) > RESPONSE_BYTES: raise ValueError('Decoded response capacity')
            (target / 'response.json').write_bytes(raw)
            self.ledger.finish('requests', number, status='returned', response_sha256=digest(raw),
                               usage=response.get('usage') if isinstance(response, dict) else None, elapsed_s=time.monotonic() - started)
            return response
        except BaseException as error:
            self.ledger.finish('requests', number, status='failed', error_type=type(error).__name__,
                               error=redact(str(error))[:2048], usage=None, elapsed_s=time.monotonic() - started)
            raise
        finally:
            if original is not None: self.transport.opener = original


def units(payload):
    """One unit per nonblank physical objective line, in order."""
    found = [(n, text) for n, text in enumerate(payload['objective'].splitlines(), 1) if text.strip()]
    if not found or len(found) > MAX_UNITS:
        raise ValueError('Unit capacity')
    return found


def prompt(payload, line, text):
    """Shared evidence prefix (identical across a case) followed by the unit assignment."""
    raw = render(payload) + '\n\nASSIGNMENT: ' + encoded({'line': line, 'text': text}).decode()
    if len(raw.encode()) > CAPACITY + 8192:
        raise ValueError('Unit prompt capacity')
    return raw


def validate_unit(value, payload, line):
    report = validate_diagnosis(value, payload)
    if any(line not in finding['requirements'] for finding in value['findings']):
        raise ValueError('Finding outside assigned requirement')
    return report


def final_message(response):
    choices = response.get('choices') if isinstance(response, dict) else None
    if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
        raise ValueError('Final choices')
    choice = choices[0]; message = choice.get('message')
    if not isinstance(message, dict) or message.get('role') != 'assistant' or message.get('function_call') is not None:
        raise ValueError('Final authority')
    calls = message.get('tool_calls')
    if calls is not None and (not isinstance(calls, list) or calls):
        raise ValueError('No tool authority')
    content = message.get('content')
    if choice.get('finish_reason') != 'stop' or not isinstance(content, str) or len(content.encode()) > 16384:
        raise ValueError('Final text/length')
    reasoning = message.get('reasoning_content') or ''
    if not isinstance(reasoning, str):
        raise ValueError('Reasoning type')
    return content, reasoning


def meter(transport, text):
    """Non-generative token count of the returned reasoning."""
    value = transport.request('/tokenize', {'content': text}, timeout=30, max_response_bytes=METER_BYTES)
    tokens = value.get('tokens') if isinstance(value, dict) else None
    if not isinstance(tokens, list):
        raise ValueError('Metering response')
    return len(tokens)


def run_unit(root, payload, line, text, config, deadline, transport=None):
    """Exactly one precharged completion; result is accepted, exhausted, invalid or failed."""
    root = Path(root); root.parent.mkdir(mode=0o700, exist_ok=True); root.mkdir(mode=0o700)
    result = {'line': line, 'text': text}
    try:
        ledger = create_ledger(root, deadline); client = UnitClient(config, ledger, transport)
        body = prompt(payload, line, text)
        result['prompt_sha256'] = digest(body.encode())
        response = client.complete([{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': body}])
    except Exception as error:
        result.update(status='failed', error_type=type(error).__name__, error=redact(str(error))[:2048])
        save(root / 'unit-result.json', result); return result
    result['usage'] = response.get('usage'); result['timings'] = response.get('timings')
    try:
        content, reasoning = final_message(response)
        count = meter(client.transport, reasoning)
        result['reasoning_tokens'] = count
        save(root / 'metering.json', {'reasoning_tokens': count, 'budget': REASONING_BUDGET,
                                      'reasoning_sha256': digest(reasoning.encode())})
    except Exception as error:
        result.update(status='invalid', error_type=type(error).__name__, error=redact(str(error))[:2048])
        save(root / 'unit-result.json', result); return result
    try:
        value = json.loads(content); report = validate_unit(value, payload, line)
        save(root / 'diagnosis.json', value); save(root / 'report.json', report)
        result.update(diagnosis=value, report_sha256=digest(encoded(report)))
        result['status'] = 'exhausted' if count >= REASONING_BUDGET else 'accepted'
    except Exception as error:
        result.update(status='exhausted' if count >= REASONING_BUDGET else 'invalid',
                      error_type=type(error).__name__, error=redact(str(error))[:2048])
    save(root / 'unit-result.json', result)
    return result


def aggregate(results, expected_units):
    if len(results) != expected_units or any(r.get('status') != 'accepted' for r in results):
        return 'incomplete'
    decisions = [r['diagnosis']['decision'] for r in results]
    if 'repair' in decisions: return 'repair'
    if 'needs_input' in decisions: return 'needs_input'
    return 'pass'


def case_work(spec_path):
    spec_path = Path(spec_path); spec = json.loads(read_file(spec_path)); root = spec_path.parent
    manifest = verify_packages(spec['manifest'], spec['manifest_sha256']); case = manifest['cases'][spec['index']]
    payload = json.loads(read_file(Path(spec['manifest']).parent / case['payload']))
    config = json.loads(read_file(spec['config'])); planned = units(payload); results = []
    for number, (line, text) in enumerate(planned, 1):
        remaining = spec['deadline'] - time.monotonic()
        if remaining < 10:
            results.append({'line': line, 'status': 'not_started', 'reason': 'Case deadline'}); break
        result = run_unit(root / 'units' / f'{number:02d}', payload, line, text, config,
                          time.monotonic() + min(UNIT_SECONDS, remaining))
        results.append(result); journal(root, 'unit_finished', line=line, status=result['status'])
        if result['status'] == 'failed':
            break
    verify_packages(spec['manifest'], spec['manifest_sha256'])
    decision = aggregate(results, len(planned))
    return {'status': 'accepted' if decision != 'incomplete' else 'incomplete', 'decision': decision,
            'units': results, 'planned_units': len(planned), 'payload_sha256': digest(encoded(payload)),
            'meaning': 'Saved-evidence per-requirement diagnosis; independent semantics pending'}


def reverify(child, payload):
    """Recompute aggregate from durable unit diagnoses instead of trusting the child summary."""
    planned = units(payload)
    if child.get('planned_units') != len(planned) or child.get('payload_sha256') != digest(encoded(payload)):
        return False
    results = child.get('units', [])
    for result, (line, _) in zip(results, planned):
        if result.get('line') != line: return False
        if result.get('status') == 'accepted':
            if result.get('reasoning_tokens', REASONING_BUDGET) >= REASONING_BUDGET: return False
            if digest(encoded(validate_unit(result['diagnosis'], payload, line))) != result['report_sha256']: return False
    return aggregate(results, len(planned)) == child.get('decision')


def batch(args):
    manifest = verify_packages(args.manifest, args.manifest_sha256)
    output = Path(args.output).resolve(); output.mkdir(mode=0o700)
    save(output / 'experiment.json', {'kind': 'per-requirement-review-units', 'manifest_sha256': args.manifest_sha256,
         'requests_per_unit': 1, 'commands': 0, 'unit_seconds': UNIT_SECONDS, 'cleanup_seconds': 150,
         'reasoning_budget': REASONING_BUDGET, 'max_units': MAX_UNITS})
    cancelled = []; results = []
    previous = {n: signal.signal(n, lambda *_: cancelled.append(True)) for n in (signal.SIGINT, signal.SIGTERM)}
    try:
        with pilot_lease(args.lease):
            for index, case in enumerate(manifest['cases']):
                verify_packages(args.manifest, args.manifest_sha256)
                payload = json.loads(read_file(Path(args.manifest).parent / case['payload']))
                root = output / case['id']; root.mkdir(mode=0o700)
                record = lambda value: journal(root, 'serving_probe', **value)
                if not wait_idle(args.config, args.identity, time.monotonic() + 30, record, lambda: bool(cancelled)):
                    results.append({'case': case['id'], 'status': 'not_started', 'reason': 'Serving idle unconfirmed'}); break
                deadline = time.monotonic() + UNIT_SECONDS * len(units(payload))
                spec = {key: str(Path(getattr(args, key)).resolve()) for key in ('manifest', 'config')}
                spec.update(index=index, manifest_sha256=args.manifest_sha256, deadline=deadline - 5)
                save(root / 'spec.json', spec)
                result = supervise([sys.executable, str(Path(__file__).resolve()), '_case', '--spec', str(root / 'spec.json')],
                                   root / 'controller.log', deadline, cancelled=lambda: bool(cancelled))
                cleanup_deadline = result.pop('cleanup_deadline')
                try: result['idle_confirmed'] = wait_idle(args.config, args.identity, cleanup_deadline, record)
                except Exception as error: result.update(idle_confirmed=False, cleanup_error=type(error).__name__)
                result['cleanup_confirmed'] = result['client_group_absent']
                child = json.loads(read_file(root / 'child-result.json')) if (root / 'child-result.json').exists() else {}
                intact = False
                try:
                    verify_packages(args.manifest, args.manifest_sha256); intact = reverify(child, payload)
                except Exception as error:
                    result['integrity_error'] = type(error).__name__
                completed = (not cancelled and not result['stop'] and result['exit_code'] == 0 and result['client_group_absent']
                             and result['work_finished_before_deadline'] and result['idle_confirmed'] and intact
                             and child.get('status') == 'accepted')
                result.update(case=case['id'], status='accepted' if completed else 'incomplete',
                              decision=child.get('decision', 'incomplete'), child=child, kind='per-requirement-review-units')
                result = publish_result(root / 'result.json', result, deadline, lambda: bool(cancelled)); results.append(result)
                save(output / 'results.json', results)
                if (cancelled or result['stop'] == 'cancelled' or not result['client_group_absent'] or not result['idle_confirmed']
                        or result['exit_code'] != 0):
                    break
    finally:
        for n, handler in previous.items(): signal.signal(n, handler)
    save(output / 'results.json', results)
    save(output / 'artifact-hashes.json', {str(p.relative_to(output)): digest(read_file(p))
                                           for p in sorted(output.rglob('*')) if p.is_file()})
    return results


def score(results_path, expectations_path):
    """Classification/completeness against private expectations; grounding is assessed separately."""
    results = {r['case']: r for r in json.loads(Path(results_path).read_bytes())}
    rows = []
    for item in json.loads(Path(expectations_path).read_bytes()):
        r = results.get(item['id'], {}); units_ = r.get('child', {}).get('units', [])
        rows.append({'case': item['id'], 'expected': item['expected'], 'decision': r.get('decision', 'missing'),
                     'status': r.get('status', 'missing'), 'match': r.get('status') == 'accepted' and r.get('decision') == item['expected'],
                     'units': len(units_), 'unit_status': [u.get('status') for u in units_],
                     'repair_lines': [u['line'] for u in units_ if u.get('diagnosis', {}).get('decision') == 'repair'],
                     'reasoning_tokens': [u.get('reasoning_tokens') for u in units_]})
    return {'matched': sum(r['match'] for r in rows), 'cases': len(rows), 'rows': rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__); sub = parser.add_subparsers(dest='command', required=True)
    run = sub.add_parser('run')
    for key in ('manifest', 'manifest-sha256', 'config', 'identity', 'output'): run.add_argument('--' + key, required=True)
    run.add_argument('--lease', default=str(Path('~/.local/state/gflo-planning-pilot/lease').expanduser()))
    child = sub.add_parser('_case'); child.add_argument('--spec', required=True)
    scoring = sub.add_parser('score'); scoring.add_argument('--results', required=True); scoring.add_argument('--expectations', required=True)
    args = parser.parse_args()
    if args.command == 'run': batch(args)
    elif args.command == 'score': print(json.dumps(score(args.results, args.expectations), indent=2))
    else:
        try: result = case_work(args.spec)
        except BaseException as error:
            save(Path(args.spec).parent / 'child-result.json', {'status': 'incomplete', 'error_type': type(error).__name__,
                                                                'error': redact(str(error))[:2048]}); return 1
        save(Path(args.spec).parent / 'child-result.json', result)
    return 0


if __name__ == '__main__': raise SystemExit(main())
