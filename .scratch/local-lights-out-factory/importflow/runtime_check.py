"""Finite larger-payload and real HTTP qualification, independent of worker gates."""
import hashlib
import http.client
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from blobs import put_blob
from jobs import Store


def request(port, method, path, body=None, key=None):
    conn=http.client.HTTPConnection('127.0.0.1',port,timeout=90)
    headers={} if key is None else {'Idempotency-Key':key,'Content-Type':'text/csv'}
    conn.request(method,path,body=body,headers=headers,encode_chunked=body is not None and not isinstance(body,bytes))
    response=conn.getresponse();data=response.read();status=response.status;conn.close()
    return status,json.loads(data)


with tempfile.TemporaryDirectory() as folder:
    db=Path(folder)/'jobs.db';root=Path(folder)/'payloads'
    sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1];sock.close()
    server=subprocess.Popen([sys.executable,'-m','api','--db',str(db),'--blobs',str(root),'--port',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
    try:
        for _ in range(100):
            if server.poll() is not None: raise AssertionError(('server stopped',server.stderr.read()))
            try:
                status,data=request(port,'GET','/health')
                if status==200: break
            except OSError: pass
            time.sleep(.05)
        else: raise AssertionError('server did not start')
        # Large number of rows but only one normalized label: bounded aggregation.
        header=b'label,quantity\n';row=b'x'+b' '*117+b',1\n'
        rows=(64*1024*1024-len(header))//len(row)
        payload_bytes=len(header)+rows*len(row)
        def upload():
            yield header
            remaining=rows
            while remaining:
                n=min(500,remaining);yield row*n;remaining-=n
        started=time.monotonic()
        status,job=request(port,'POST','/imports',upload(),'large')
        assert status==202,(status,job)
        upload_seconds=time.monotonic()-started
        work=subprocess.run([sys.executable,'-m','worker','--db',str(db),'--blobs',str(root),'--once'],capture_output=True,text=True,timeout=90)
        assert work.returncode==0,(work.stdout,work.stderr)
        status,result=request(port,'GET','/imports/'+job['id']+'/result')
        assert status==200 and result==[dict(label='x',quantity=rows)],(status,result)
        processing_seconds=time.monotonic()-started-upload_seconds
        status,duplicate=request(port,'POST','/imports',upload(),'large')
        assert status==202 and duplicate['id']==job['id'] and duplicate['status']=='succeeded',duplicate
        status,conflict=request(port,'POST','/imports',b'label,quantity\nx,2\n','large')
        assert status==409,(status,conflict)
        def oversized():
            for _ in range(1024): yield b'x'*65536
            yield b'x'
        status,detail=request(port,'POST','/imports',oversized(),'too-large')
        assert status==413,(status,detail)
        # Stop HTTP server before worker load to separate the measurements.
        server.terminate();server.wait(timeout=10)
        store=Store(db);small=put_blob(root,[b'label,quantity\nx,1\n'])
        batch=[store.submit('load-'+str(i),'inventory_csv',small) for i in range(500)]
        command="from jobs import Store; from worker import run_once,csv_handler; import sys; s=Store(sys.argv[1]);\nwhile run_once(s,sys.argv[2],{'inventory_csv':csv_handler}): pass"
        started=time.monotonic()
        workers=[subprocess.Popen([sys.executable,'-c',command,str(db),str(root)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for _ in range(4)]
        for proc in workers:
            out,err=proc.communicate(timeout=60);assert proc.returncode==0,(out,err)
        elapsed=time.monotonic()-started
        for item in batch:
            result=store.get(item['id'])
            assert result['status']=='succeeded' and result['attempts']==1 and result['result']==[dict(label='x',quantity=1)],result
        print(json.dumps(dict(upload_bytes=payload_bytes,rows=rows,upload_seconds=upload_seconds,processing_seconds=processing_seconds,workers=4,jobs=500,job_seconds=elapsed,jobs_per_second=500/elapsed,idempotency_passed=True,oversize_rejected=True)))
    finally:
        if server.poll() is None:
            server.terminate()
            try:server.wait(timeout=5)
            except subprocess.TimeoutExpired:server.kill();server.wait()
        if server.stderr:server.stderr.close()
