import argparse
import re
import tempfile
from fastapi import FastAPI, HTTPException, Request
from blobs import put_blob
from jobs import Store


def create_app(db_path, blob_root, max_upload_bytes=67108864):
    app = FastAPI()
    store = Store(db_path)

    @app.get('/health')
    def health():
        return {'status':'ok'}

    @app.post('/imports',status_code=202)
    async def submit(request: Request):
        key = request.headers.get('Idempotency-Key')
        if not key or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',key):
            raise HTTPException(400,'invalid idempotency key')
        with tempfile.TemporaryFile() as spool:
            size = 0
            async for chunk in request.stream():
                size += len(chunk)
                if size > max_upload_bytes:
                    raise HTTPException(413,'upload too large')
                spool.write(chunk)
            spool.seek(0)
            digest = put_blob(blob_root,iter(lambda:spool.read(65536),b''),max_upload_bytes)
        try:
            return store.submit(key,'inventory_csv',digest)
        except OverflowError:
            raise HTTPException(429,'queue full')
        except ValueError as exc:
            raise HTTPException(409,str(exc))

    @app.get('/imports/{job_id}')
    def status(job_id: str):
        job = store.get(job_id)
        if job is None:
            raise HTTPException(404,'unknown job')
        return job

    @app.get('/imports/{job_id}/result')
    def result(job_id: str):
        job = status(job_id)
        if job['status'] != 'succeeded':
            raise HTTPException(409,'result unavailable')
        return job['result']
    return app


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--db',required=True)
    parser.add_argument('--blobs',required=True)
    parser.add_argument('--host',default='127.0.0.1')
    parser.add_argument('--port',type=int,default=8000)
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code)
    import uvicorn
    uvicorn.run(create_app(args.db,args.blobs),host=args.host,port=args.port)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
