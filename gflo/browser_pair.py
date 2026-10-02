"""One disposable owner-EOF guardian for an application/browser pair."""
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import threading
import time

CLEANUP_SECONDS = 130  # In-flight create30 + removals60 + readback15 + joins10 + margin15.


def run(spec, output, *, cancelled=lambda:False):
    process=subprocess.Popen([sys.executable,'-m','gflo.browser_pair'],stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    errors=[];tail=bytearray();count=[0];overflow=threading.Event()
    def copy():
        try:
            while True:
                data=process.stdout.read(65536)
                if not data:break
                count[0]+=len(data)
                if count[0]>24*1024*1024+65536:overflow.set();continue
                output.write(data)
        except Exception as error:errors.append(str(error));overflow.set()
    def logs():
        while True:
            data=process.stderr.read(4096)
            if not data:break
            tail.extend(data)
            if len(tail)>16384:del tail[:-16384]
    readers=[threading.Thread(target=copy,daemon=True),threading.Thread(target=logs,daemon=True)]
    reason=None;started=time.monotonic()
    try:
        process.stdin.write((json.dumps(spec)+'\n').encode());process.stdin.flush()
        for reader in readers:reader.start()
        while process.poll() is None:
            if cancelled():reason='cancelled';break
            if overflow.is_set():reason='artifact_limit';break
            if time.monotonic()-started>=110:reason='deadline';break
            time.sleep(.05)
    finally:
        process.stdin.close()
        try:process.wait(timeout=CLEANUP_SECONDS)
        except subprocess.TimeoutExpired:
            process.kill();process.wait(timeout=5)
            raise RuntimeError('Browser pair guardian cleanup uncertain; explicit recovery required')
        finally:
            for reader in readers:
                if reader.ident is not None:reader.join(timeout=5)
            process.stdout.close();process.stderr.close()
    if any(reader.is_alive() for reader in readers):raise RuntimeError('Browser transport cleanup uncertain')
    facts_path=Path(spec['facts'])
    facts=json.loads(facts_path.read_bytes()) if facts_path.exists() else {}
    return {'exit_code':process.returncode,'reason':reason,'diagnostics':tail.decode(errors='replace'),
            'transport_errors':errors,'facts':facts,'elapsed_s':time.monotonic()-started}


def main():
    spec=json.loads(sys.stdin.buffer.readline(65537));started=time.monotonic()
    app=browser=None;facts={'containers':{},'cleanup':{'confirmed':False},'failure':None}
    names=[spec['browser_name'],spec['app_name']]
    def alive():
        if time.monotonic()-started>=110:raise TimeoutError('Pair work deadline')
        if select.select([sys.stdin.buffer],[],[],0)[0] and not sys.stdin.buffer.read(1):raise InterruptedError('Pair owner EOF')
    def docker(args,timeout=15):
        alive()
        return subprocess.run(['docker',*args],capture_output=True,timeout=timeout,check=True)
    def create(args,name):
        if args[:3]!=['docker','run','--rm'] or '--name' not in args or args[args.index('--name')+1]!=name:
            raise ValueError('Invalid fixed pair command')
        result=docker(['create',*args[3:]],30)
        identifier=result.stdout.decode().strip()
        if len(identifier)!=64 or any(c not in '0123456789abcdef' for c in identifier):raise ValueError('Invalid created container ID')
        inspected=json.loads(docker(['inspect',identifier]).stdout)[0]
        if inspected['Id']!=identifier:raise ValueError('Container identity changed')
        expected=spec['app_image'] if name==spec['app_name'] else spec['browser_image']
        if inspected['Image']!=expected:raise ValueError('Container image identity changed')
        facts['containers'][name]={'id':identifier,'image':inspected['Image'],'host':inspected['HostConfig'],
                                  'config':{k:inspected['Config'].get(k) for k in ['User','Env','WorkingDir','Entrypoint','Cmd']},
                                  'mounts':inspected['Mounts']}
        alive()
        return identifier
    code=1
    try:
        app_id=create(spec['app_args'],spec['app_name'])
        app=subprocess.Popen(['docker','start','-a',app_id],stdin=subprocess.DEVNULL,stdout=sys.stderr,stderr=sys.stderr)
        args=list(spec['browser_args'])
        index=args.index('--network')+1
        if args[index]!='OWNED_APP':raise ValueError('Invalid network namespace placeholder')
        args[index]='container:'+app_id
        browser_id=create(args,spec['browser_name'])
        if app.poll() is not None:raise RuntimeError('Application exited during browser startup')
        browser=subprocess.Popen(['docker','start','-a',browser_id],stdin=subprocess.DEVNULL,stdout=sys.stdout,stderr=sys.stderr)
        while browser.poll() is None:
            alive()
            if app.poll() is not None:raise RuntimeError('Application exited during journey/artifact capture')
            time.sleep(.05)
        if app.poll() is not None:raise RuntimeError('Application exited before artifact completion')
        code=browser.returncode
    except BaseException as error:
        facts['failure']={'kind':type(error).__name__,'message':str(error)[:4096]}
        print(str(error)[:4096],file=sys.stderr)
    finally:
        errors=[]
        for name in names:
            try:
                result=subprocess.run(['docker','rm','-f',name],capture_output=True,timeout=30)
                if result.returncode and b'No such container' not in result.stderr:
                    errors.append(result.stderr.decode(errors='replace')[:1024])
            except Exception as error:errors.append(str(error)[:1024])
        for process in (browser,app):
            if process is not None:
                if process.poll() is None:process.kill()
                try:process.wait(timeout=5)
                except subprocess.TimeoutExpired:errors.append('Attached container process did not exit')
        try:
            result=subprocess.run(['docker','ps','-aq','--no-trunc','--filter','label=gflo.browser.run='+spec['run']],
                                  capture_output=True,check=True,timeout=15)
            remaining=result.stdout.decode().split()
            facts['cleanup']={'confirmed':not remaining and not errors,'remaining':remaining,'errors':errors}
        except Exception as error:
            facts['cleanup']={'confirmed':False,'errors':errors+[str(error)[:1024]]}
        facts['elapsed_s']=time.monotonic()-started
        with open(spec['facts'],'x') as stream:json.dump(facts,stream)
    return code if facts['cleanup']['confirmed'] else 125


if __name__=='__main__':raise SystemExit(main())
