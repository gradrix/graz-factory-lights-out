"""Independent random parser oracle and multiple worker-process completion audit."""
import csv
import io
import json
import random
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from tabular import summarize
from blobs import put_blob
from jobs import Store

rng=random.Random(87521)
for _ in range(30):
    totals={};stream=io.StringIO(newline='');writer=csv.writer(stream)
    writer.writerow(['label','quantity'])
    for _ in range(100):
        label=rng.choice(['a','A','ž','comma,label','quote"label'])
        qty=rng.randint(-1000,1000)
        writer.writerow([' '+label+' ',str(qty)])
        totals[label]=totals.get(label,0)+qty
    stream.seek(0)
    assert summarize(stream)==[dict(label=k,quantity=totals[k]) for k in sorted(totals)]
with tempfile.TemporaryDirectory() as folder:
    db=Path(folder)/'db';root=Path(folder)/'blobs';store=Store(db)
    payload=put_blob(root,[b'label,quantity\nx,1\n'])
    jobs=[store.submit('batch-'+str(n),'inventory_csv',payload) for n in range(100)]
    script="from jobs import Store; from worker import run_once,csv_handler; import sys; s=Store(sys.argv[1]);\nwhile run_once(s,sys.argv[2],{'inventory_csv':csv_handler}): pass"
    started=time.monotonic()
    procs=[subprocess.Popen([sys.executable,'-c',script,str(db),str(root)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for _ in range(4)]
    for proc in procs:
        out,err=proc.communicate(timeout=25);assert proc.returncode==0,(out,err)
    elapsed=time.monotonic()-started
    for job in jobs:
        result=store.get(job['id'])
        assert result['status']=='succeeded' and result['attempts']==1 and result['result']==[dict(label='x',quantity=1)],result
        assert store.submit(job['key'],job['kind'],job['payload'])==result
    assert elapsed<25,elapsed
print('heldout-ok')
