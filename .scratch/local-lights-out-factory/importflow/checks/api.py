import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from api import create_app
from jobs import Store
from worker import run_once,csv_handler

with tempfile.TemporaryDirectory() as folder:
    db=Path(folder)/'db';root=Path(folder)/'blobs'
    client=TestClient(create_app(db,root,max_upload_bytes=100))
    assert client.get('/health').json()=={'status':'ok'}
    raw=b'label,quantity\nx,2\n';headers={'Idempotency-Key':'batch-1'}
    response=client.post('/imports',headers=headers,content=raw)
    assert response.status_code==202,(response.status_code,response.text)
    job=response.json();assert job['status']=='queued'
    assert client.post('/imports',headers=headers,content=raw).json()==job
    assert client.post('/imports',headers=headers,content=raw+b'x,1\n').status_code==409
    assert client.post('/imports',content=raw).status_code==400
    assert client.post('/imports',headers={'Idempotency-Key':'bad space'},content=raw).status_code==400
    assert client.post('/imports',headers={'Idempotency-Key':'large'},content=b'x'*101).status_code==413
    assert client.get('/imports/unknown').status_code==404
    assert client.get('/imports/unknown/result').status_code==404
    assert client.get('/imports/'+job['id']+'/result').status_code==409
    assert run_once(Store(db),root,{'inventory_csv':csv_handler},now=1)
    assert client.get('/imports/'+job['id']+'/result').json()==[dict(label='x',quantity=2)]
    again=TestClient(create_app(db,root))
    assert again.get('/imports/'+job['id']).json()['status']=='succeeded'
    invalid=again.post('/imports',headers={'Idempotency-Key':'invalid'},content=b'\xff')
    assert invalid.status_code==202
    assert run_once(Store(db),root,{'inventory_csv':csv_handler},now=2)
    bad=again.get('/imports/'+invalid.json()['id']).json()
    assert bad['status']=='failed' and 'row ' in bad['error'],bad
print('api-ok')
