#!/usr/bin/env python3
"""Independent supplemental B1-B5 probes; run ONLY in approved offline readonly container."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request


def tree(root):
    result = {}
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise ValueError('Probe does not follow candidate symlinks')
        if path.is_file():
            result[str(path.relative_to(root))] = [path.stat().st_mode & 0o777,
                hashlib.sha256(path.read_bytes()).hexdigest()]
    return result


def equal(actual, expected):
    assert type(actual) is type(expected), (actual, expected)
    if isinstance(expected, dict):
        assert actual.keys() == expected.keys(), (actual, expected)
        for key in expected: equal(actual[key], expected[key])
    elif isinstance(expected, list):
        assert len(actual) == len(expected), (actual, expected)
        for left, right in zip(actual, expected): equal(left, right)
    else:
        assert actual == expected, (actual, expected)


def operation(kind, path, value=None):
    return {'op': kind, 'path': path, **({} if kind == 'remove' else {'value': value})}


def chain(depth, leaf=0):
    for _ in range(depth): leaf = {'a': leaf}
    return leaf


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    args = parser.parse_args()
    assert sys.version_info[:3] == (3, 12, 13), 'Requires approved CPython3.12.13 image'
    project = args.project.resolve()
    before = tree(project)
    results = []
    def probe(name, callback):
        try:
            evidence = callback()
            results.append({'name': name, 'passed': True, **({'output': evidence[-3000:]} if isinstance(evidence, str) else {})})
        except Exception as error:
            results.append({'name': name, 'passed': False, 'type': type(error).__name__, 'detail': str(error)[:1000]})
    with tempfile.TemporaryDirectory(prefix='gflo-api-independent-') as temporary:
        scratch = Path(temporary)
        build, wheels, site, arbitrary = [scratch / name for name in ('build', 'wheels', 'site', 'arbitrary-cwd')]
        shutil.copytree(project, build)
        for path in (wheels, site, arbitrary): path.mkdir()
        env = dict(os.environ, PYTHONPATH='/opt/deps', PYTHONDONTWRITEBYTECODE='1', PIP_NO_INDEX='1')
        def command(argv, cwd=arbitrary, timeout=30):
            outcome = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
            assert outcome.returncode == 0, (outcome.returncode, outcome.stdout[-3000:], outcome.stderr[-3000:])
            return outcome
        command([sys.executable, '-c', 'import setuptools.build_meta as b; b.build_wheel(' + repr(str(wheels)) + ')'], build)
        candidates = list(wheels.glob('*.whl')); assert len(candidates) == 1
        command([sys.executable, '-m', 'pip', 'install', '--no-index', '--no-deps', '--target', str(site), str(candidates[0])])
        env['PYTHONPATH'] = str(site) + ':/opt/deps'
        sys.path[:0] = [str(site), '/opt/deps']
        from config_preview.domain import preview
        from config_preview.errors import Conflict
        from config_preview.audit import event
        def direct(base, operations, expected_document=None, error=None):
            original = copy.deepcopy([base, operations])
            try:
                result = preview(base, operations)
            except Conflict as failure:
                assert error == ('conflict', failure.index, failure.code), (error, failure.index, failure.code)
                assert type(failure.index) is int
            except ValueError:
                assert error == 'shape', error
            else:
                assert error is None, ('Expected rejection', error, result)
                equal(result['document'], expected_document)
                return result
            finally:
                equal([base, operations], original)
        valid = [
            ('depth6-at-limit', chain(6), [], chain(6)),
            ('200-nodes-empty-operations', {f'k{i}': 0 for i in range(199)}, [], {f'k{i}': 0 for i in range(199)}),
            ('replace-at-node-limit', {f'k{i}': 0 for i in range(199)}, [operation('set', ['k0'], None)], {**{f'k{i}': 0 for i in range(199)}, 'k0': None}),
            ('unicode80-and-int-extremes', {}, [operation('set', ['s'], '😀'*80), operation('set', ['lo'], -1000000), operation('set', ['hi'], 1000000)], {'s':'😀'*80, 'lo':-1000000, 'hi':1000000}),
            ('50-operations', {'a': 0}, [operation('set', ['a'], i) for i in range(50)], {'a':49}),
            ('nested-exact-test-key-order', {'a':{'x':True,'y':0}}, [operation('test',['a'],{'y':0,'x':True})], {'a':{'x':True,'y':0}}),
        ]
        invalid = [
            ('depth7-base', chain(7), []),
            ('201-nodes-base', {f'k{i}':0 for i in range(200)}, []),
            ('unicode81', {}, [operation('set',['a'],'😀'*81)]),
            ('negative-int-overflow', {'a':-1000001}, []),
            ('non-ascii-key', {'é':0}, []),
            ('key32-valid-prefix33', {'a'*33:0}, []),
            ('operations-object', {}, {}),
            ('operation-null', {}, [None]),
            ('op-boolean', {}, [{'op':True,'path':['a'],'value':0}]),
            ('path-string', {}, [operation('set','a',0)]),
            ('path-boolean', {}, [operation('set',[True],0)]),
            ('path7', {}, [operation('set',['a']*7,0)]),
            ('missing-set-value', {}, [{'op':'set','path':['a']}]),
            ('nested-float', {}, [operation('set',['a'],{'n':0.0})]),
            ('late-invalid-preempts-conflict', {}, [operation('remove',['missing']),operation('set',['a'],chain(7))]),
            ('late-node-overflow-preempts-conflict', {}, [operation('remove',['missing']),operation('set',['a'],{f'k{i}':0 for i in range(200)})]),
        ]
        conflicts = [
            ('insert-valid-value-exceeds-total-nodes', {}, [operation('set',['a'],{f'k{i}':0 for i in range(199)})], 0,'limit'),
            ('insert-valid-value-exceeds-total-depth', chain(5,{}), [operation('set',['a']*6,{'x':0})],0,'limit'),
            ('nested-true-versus-one', {'a':{'x':True}}, [operation('test',['a'],{'x':1})],0,'test_failed'),
            ('nested-zero-versus-false', {'a':{'x':0}}, [operation('test',['a'],{'x':False})],0,'test_failed'),
            ('later-limit-is-atomic', {f'k{i}':0 for i in range(198)}, [operation('set',['new'],1),operation('set',['overflow'],2)],1,'limit'),
        ]
        for name, base, operations, want in valid:
            probe('API/'+name, lambda b=base,o=operations,w=want: direct(b,o,w))
        for name, base, operations in invalid:
            probe('API/'+name, lambda b=base,o=operations: direct(b,o,error='shape'))
        for name, base, operations, index, code in conflicts:
            probe('API/'+name, lambda b=base,o=operations,i=index,c=code: direct(b,o,error=('conflict',i,c)))
        def aliases():
            base={'keep':{'x':0}}; value={'x':1}; path=['added']
            operations=[operation('set',path,value),operation('set',['added','x'],2)]
            result=direct(base,operations,{'keep':{'x':0},'added':{'x':2}})
            equal(result['audit'][0]['after'],{'present':True,'value':{'x':1}})
            base['keep']['x']=9; value['x']=9; path.append('changed')
            equal(result['document'],{'keep':{'x':0},'added':{'x':2}})
            equal(result['audit'][0]['path'],['added'])
            equal(result['audit'][0]['after'],{'present':True,'value':{'x':1}})
            before_value={'x':{'y':1}}; after_value={'x':{'y':2}}; copied_path=['a']
            item=event(0,'set',copied_path,True,before_value,True,after_value)
            before_value['x']['y']=9; after_value['x']['y']=9; copied_path.append('changed')
            equal(item,{'index':0,'op':'set','path':['a'],'before':{'present':True,'value':{'x':{'y':1}}},'after':{'present':True,'value':{'x':{'y':2}}}})
        probe('API/audit-snapshots-and-input-aliasing',aliases)
        sock=socket.socket(); sock.bind(('127.0.0.1',0)); port=sock.getsockname()[1]; sock.close()
        server=subprocess.Popen([sys.executable,'-m','uvicorn','config_preview.app:app','--host','127.0.0.1','--port',str(port),'--log-level','error'],cwd=arbitrary,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        def http(body,path='/config/preview',raw=False):
            request=urllib.request.Request(f'http://127.0.0.1:{port}'+path,data=body if raw else json.dumps(body).encode(),headers={'Content-Type':'application/json'})
            try:
                with urllib.request.urlopen(request,timeout=3) as response:return response.status,json.load(response)
            except urllib.error.HTTPError as response:return response.code,json.load(response)
        try:
            deadline=time.monotonic()+8
            while True:
                try: http({'base':{},'operations':[]}); break
                except OSError:
                    if time.monotonic()>deadline:raise
                    time.sleep(.05)
            def status(body,wanted): equal(http(body)[0],wanted)
            for name,base,operations,want in valid:
                def success(b=base,o=operations,w=want):
                    code,body=http({'base':b,'operations':o});equal(code,200);equal(body['document'],w)
                probe('HTTP/'+name,success)
            for name,base,operations in invalid:
                probe('HTTP/'+name,lambda b=base,o=operations:status({'base':b,'operations':o},422))
            for name,base,operations,index,code in conflicts:
                def conflict(b=base,o=operations,i=index,c=code):
                    status_code,body=http({'base':b,'operations':o});equal(status_code,409);equal(body,{'error':{'index':i,'code':c}})
                probe('HTTP/'+name,conflict)
            for name,payload in [('top-null',None),('top-array',[]),('missing-base',{'operations':[]}),('missing-operations',{'base':{}}),('base-null',{'base':None,'operations':[]})]:
                probe('HTTP/'+name,lambda body=payload:status(body,422))
            probe('HTTP/malformed-json',lambda:equal(http(b'{','/config/preview',True)[0],422))
            probe('HTTP/stateless-after-conflicts',lambda:equal(http({'base':{},'operations':[]})[1],{'document':{},'audit':[]}))
        finally:
            server.terminate()
            try:server.wait(timeout=5)
            except subprocess.TimeoutExpired:server.kill();server.wait(timeout=2)
        def generated_tests():
            outcome=command([sys.executable,'-m','unittest','discover','-s',str(project)],timeout=30)
            return outcome.stdout+outcome.stderr
        probe('B5/installed-unittest-from-arbitrary-cwd',generated_tests)
        readme=(project/'README.md').read_text()
        docs={'words':len(readme.split()),'command_lines':[line for line in readme.splitlines() if any(token in line for token in ('uvicorn','unittest','python ','pip '))],
              'note':'Command lines are evidence for semantic review, not keyword acceptance. The mandated installed-package unittest and app-target commands ran above.'}
    equal(tree(project),before)
    print(json.dumps({'supplemental_only':True,'project_unchanged':True,'probes':results,'documentation':docs,'passed':all(item['passed'] for item in results)},indent=2))
    return 0 if all(item['passed'] for item in results) else 1


if __name__=='__main__': raise SystemExit(main())
