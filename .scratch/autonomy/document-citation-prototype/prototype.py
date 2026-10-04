"""PRIVATE DISCOVERY ONLY: fixed four-case comparison, no runtime mutation."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

ROOT = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(ROOT / 'source'))
from gflo.documents import answer_request, bounded_answer, decode, validate_answer
from gflo.worker import ModelWorker


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=True, indent=2) + '\n')


def refs(value, evidence):
    """Validate references before deriving a complete, unchanged source span."""
    result = copy.deepcopy(value)
    if not isinstance(result, dict) or not isinstance(result.get('claims'), list):
        raise ValueError('Invalid reference answer shape')
    for claim in result['claims']:
        if not isinstance(claim, dict) or not isinstance(claim.get('citations'), list):
            raise ValueError('Invalid reference claim')
        for cite in claim['citations']:
            if (not isinstance(cite, dict) or set(cite) != {'evidence_id', 'span'} or
                    cite['evidence_id'] != evidence['id'] or type(cite['span']) is not int or
                    not 1 <= cite['span'] <= len(evidence['spans'])):
                raise ValueError('Invalid evidence/span reference')
            cite['excerpt'] = evidence['spans'][cite['span'] - 1]
    return validate_answer(result, evidence)


class Capture(ModelWorker):
    def request(self, path, body=None, timeout=120, *, max_response_bytes=None):
        # Use the accepted loopback-only/no-redirect client opener and key authority.
        headers = {'Content-Type': 'application/json',
                   'Authorization': 'Bearer ' + Path(self.config['api_key_file']).read_text().strip()}
        request = urllib.request.Request(self.endpoint + path, data=json.dumps(body).encode(), headers=headers)
        with self.opener.open(request, timeout=timeout) as response:
            raw = response.read(max_response_bytes + 1)
            (self.destination / 'response.raw.json').write_bytes(raw)
            if len(raw) > max_response_bytes:
                raise ValueError('Model response byte limit')
            return json.loads(raw)


def main():
    contract = json.loads((ROOT / 'contract.json').read_text())
    for name, expected in contract['input_hashes'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
    inspect = json.loads(subprocess.check_output(['docker', 'inspect', 'gflo-model']))[0]
    cmd = inspect['Config']['Cmd']
    assert cmd[cmd.index('-c') + 1] == '98304'
    assert cmd[cmd.index('--cache-type-k') + 1] == cmd[cmd.index('--cache-type-v') + 1] == 'q4_0'
    key = next(m['Source'] for m in inspect['Mounts'] if m['Destination'] == '/run/model-key')
    out = ROOT / 'results'
    out.mkdir()
    save(out / 'serving.json', {'container_id': inspect['Id'], 'image': inspect['Image'], 'command': cmd})
    client = Capture({'endpoint': 'http://127.0.0.1:18000', 'api_key_file': key}, None)
    rows = []
    for index, case in enumerate(contract['cases']):
        evidence = json.loads((ROOT / 'inputs' / (case['source'] + '.json')).read_text())
        for method in (['exact', 'references'] if index % 2 == 0 else ['references', 'exact']):
            folder = out / case['name'] / method
            folder.mkdir(parents=True)
            request = answer_request(evidence, 'flash-next-coder', case['question'])
            if method == 'references':
                request['messages'][0]['content'] = request['messages'][0]['content'].replace(
                    ',"excerpt":"exact source substring"', '') + ' Select only evidence_id and integer span in each citation. The controller derives the complete unchanged source span as the excerpt; do not produce excerpt text.'
            row = {'case': case['name'], 'method': method, 'attempts': [], 'valid': False}
            started = time.monotonic()
            for attempt in range(2):
                target = folder / str(attempt + 1)
                target.mkdir()
                client.destination = target
                save(target / 'request.json', request)
                call_started = time.monotonic()
                info = {'attempt': attempt + 1}
                try:
                    response = bounded_answer(client, request, lambda: False)
                    save(target / 'response.json', response)
                    content = response['choices'][0]['message']['content']
                    (target / 'content.txt').write_text(content)
                    info['usage'] = response.get('usage')
                    info['finish_reason'] = response['choices'][0].get('finish_reason')
                    try:
                        value = decode(content)
                        checked = validate_answer(value, evidence) if method == 'exact' else refs(value, evidence)
                        save(target / 'validated.json', checked)
                        row['valid'] = True
                        row['answer'] = checked
                    except (ValueError, KeyError, TypeError) as error:
                        info['validation_error'] = str(error)
                        if attempt == 0:
                            request['messages'] += [
                                {'role': 'assistant', 'content': content},
                                {'role': 'user', 'content': 'Controller validation failed: ' + str(error) + '. Return one corrected complete JSON answer using the original evidence and schema. Do not change source text, invent references, or treat valid provenance as proof of a claim.'}]
                except Exception as error:
                    info['request_error'] = type(error).__name__ + ': ' + str(error)
                info['elapsed_s'] = time.monotonic() - call_started
                row['attempts'].append(info)
                save(target / 'outcome.json', info)
                if row['valid'] or 'request_error' in info:
                    break
            row['elapsed_s'] = time.monotonic() - started
            rows.append(row)
            save(out / 'results.json', rows)
            print(case['name'], method, row['valid'], round(row['elapsed_s'], 3), flush=True)
    # The model service itself and source/cache files remain untouched.
    assert json.loads(subprocess.check_output(['docker', 'inspect', 'gflo-model']))[0]['Id'] == inspect['Id']
    for name, expected in contract['input_hashes'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name


if __name__ == '__main__':
    main()
