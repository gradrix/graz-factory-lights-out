import io
import pytest
from blobs import put_blob,open_blob
from tabular import summarize
from jobs import Store
from worker import run_once,csv_handler
from api import create_app
from fastapi.testclient import TestClient


def test_csv():
    assert summarize(io.StringIO('label,quantity\nz,2\na,1\nz,-2\n')) == [dict(label='a',quantity=1),dict(label='z',quantity=0)]


@pytest.mark.parametrize('raw',['label,quantity\n"\na",1\n','label,quantity\nx,"1','label,quantity\nx,١\n'])
def test_bad_csv(raw):
    with pytest.raises(ValueError,match='row 2'):
        summarize(io.StringIO(raw))


def test_blobs(tmp_path):
    key=put_blob(tmp_path,[b'abc',b'd'])
    with open_blob(tmp_path,key) as stream:
        assert stream.read()==b'abcd'
    with pytest.raises(ValueError):
        put_blob(tmp_path,[b'large'],limit=2)
    assert len(list(tmp_path.iterdir()))==1


def test_idempotency(tmp_path):
    store=Store(tmp_path/'db')
    job=store.submit('key','kind','a'*64)
    assert store.submit('key','kind','a'*64)==job
    with pytest.raises(ValueError):
        store.submit('key','other','a'*64)


def test_fencing(tmp_path):
    store=Store(tmp_path/'db')
    store.submit('key','kind','a'*64)
    first=store.claim(10,ttl=1)
    second=store.claim(11,ttl=2)
    assert not store.finish(first['id'],first['token'],11,result={'old':1})
    assert store.finish(second['id'],second['token'],11,result={'new':2})
    assert not store.finish(second['id'],second['token'],11,result={'new':2})


def test_handler_reuse(tmp_path):
    store=Store(tmp_path/'db')
    digest=put_blob(tmp_path/'blobs',[b'abcd'])
    job=store.submit('key','length',digest)
    assert run_once(store,tmp_path/'blobs',{'length':lambda stream:len(stream.read())},now=1)
    assert store.get(job['id'])['result']==4


def test_http(tmp_path):
    db=tmp_path/'db';root=tmp_path/'blobs'
    client=TestClient(create_app(db,root))
    response=client.post('/imports',headers={'Idempotency-Key':'k'},content=b'label,quantity\nx,1\n')
    assert response.status_code==202
    job=response.json()
    assert run_once(Store(db),root,{'inventory_csv':csv_handler},now=1)
    assert client.get('/imports/'+job['id']+'/result').json()==[dict(label='x',quantity=1)]
    assert client.post('/imports',content=b'').status_code==400
