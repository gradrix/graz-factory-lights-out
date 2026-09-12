import argparse
import io
import math
import time
from blobs import open_blob
from jobs import Store
from tabular import summarize


def csv_handler(stream):
    return summarize(io.TextIOWrapper(stream, encoding='utf-8', newline=''))


def run_once(store, blob_root, handlers, *, now=None, ttl=30.0):
    job = store.claim(time.time() if now is None else now, ttl)
    if job is None:
        return False
    try:
        with open_blob(blob_root, job['payload']) as stream:
            result = handlers[job['kind']](stream)
        store.finish(job['id'], job['token'], time.time() if now is None else now, result=result)
    except Exception as exc:
        store.finish(job['id'], job['token'], time.time() if now is None else now, error=(str(exc) or type(exc).__name__)[:2000])
    return True


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', required=True)
    parser.add_argument('--blobs', required=True)
    parser.add_argument('--once', action='store_true')
    parser.add_argument('--poll', type=float, default=.2)
    try:
        args = parser.parse_args(argv)
        if not math.isfinite(args.poll) or args.poll <= 0:
            parser.error('poll must be finite and positive')
    except SystemExit as exc:
        return int(exc.code)
    store = Store(args.db)
    try:
        while True:
            done = run_once(store,args.blobs,{'inventory_csv':csv_handler})
            if args.once:
                return 0
            if not done:
                time.sleep(args.poll)
    except KeyboardInterrupt:
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
