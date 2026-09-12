import asyncio
import tempfile
import tracemalloc
from pathlib import Path
from api import create_app

async def exercise(app, key, chunks, expected):
    chunks=iter(chunks);sent=[]
    async def receive():
        try: chunk=next(chunks)
        except StopIteration: return {'type':'http.request','body':b'','more_body':False}
        return {'type':'http.request','body':chunk,'more_body':True}
    async def send(message): sent.append(message)
    scope={'type':'http','asgi':{'version':'3.0'},'http_version':'1.1','method':'POST','scheme':'http','path':'/imports','raw_path':b'/imports','query_string':b'','root_path':'','headers':[(b'idempotency-key',key.encode())],'client':('127.0.0.1',1000),'server':('127.0.0.1',8000)}
    await app(scope,receive,send)
    assert sent[0]['status']==expected,sent

with tempfile.TemporaryDirectory() as folder:
    app=create_app(Path(folder)/'db',Path(folder)/'blobs',max_upload_bytes=2*1024*1024)
    # Warm up framework allocations before measuring a larger upload.
    asyncio.run(exercise(app,'warm',[b'label,quantity\n'],202))
    tracemalloc.start()
    asyncio.run(exercise(app,'large',(b'x'*65536 for _ in range(32)),202))
    _,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
    assert peak<1*1024*1024,('upload was buffered in memory',peak)
    asyncio.run(exercise(app,'oversized',(b'x'*65536 for _ in range(33)),413))
print('streaming-ok')
