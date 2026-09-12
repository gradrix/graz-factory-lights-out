# Importflow: reusable durable CSV-import service

Produce a complete Python >=3.11 project: blobs.py, tabular.py, jobs.py, worker.py,
api.py, pyproject.toml, README.md, tests/test_importflow.py. Runtime packages FastAPI
and uvicorn are provisioned; tests also have httpx and pytest. The initial repository
contains only this brief and archive/preserved.txt. Preserve both exactly. Every
output file requires a producer. Prefer one implementation file per task and concise,
complete responses; tests and README are separate tasks. Target single-host Linux,
multiple API/worker processes, local filesystem SQLite WAL. Clearly document that
multi-host scaling requires shared payload storage and another database adapter.
Implement concrete small interfaces below; durable job code must not import CSV,
FastAPI or inventory logic. No candidate source or generated tests are supplied.

## Payload module: blobs.py

Expose put_blob(root, chunks, limit=67108864)->str and open_blob(root, digest).
root is str/Path and may be created. chunks is any iterable yielding bytes; consume
incrementally, never concatenate the whole upload. At most limit bytes; limit must
be an integer >=1, not bool. Non-bytes chunks and over-limit input raise ValueError.
Write a same-directory temporary file while computing SHA-256; publish with
os.replace under lowercase 64-hex content digest. Return that digest. Empty content
is valid. Equal bytes return equal identities even with different chunk boundaries.
On iterable/write/replace failure clean temporary files and preserve existing blobs.
Never trust filenames from clients. open_blob returns a binary readable file object;
digest must fullmatch ASCII [0-9a-f]{64}, otherwise ValueError. Missing blob raises
FileNotFoundError. Files are immutable through this interface; processing never
modifies or deletes existing payloads. Bounded memory depends on chunk size, not
whole payload size. A caller owns and closes open_blob's returned handle.

## CSV module: tabular.py

Expose summarize(stream, max_rows=1000000, max_labels=1000)->list[dict], accepting
an iterable of text lines such as TextIO opened with newline=''. Parse incrementally
using csv.reader(..., strict=True). Never read all rows into a list. Exact header
label,quantity. Header alone produces []. Blank/missing/extra fields, malformed CSV,
invalid UTF-8 decoding, and invalid values raise ValueError whose text includes
'row N' (1-based logical CSV record, header=1). On decoding errors use the current
record number. csv strict dialect defines quoting validity. CR/LF row endings work.
Labels: reject CR/LF anywhere raw, then strip; 1..120 characters. Quantities fullmatch
ASCII [+-]?[0-9]{1,10}; integer magnitude <=1000000000. No whitespace, float, Unicode
digits, trailing newline or exponent. Sum per normalized label preserving Unicode
and case, include zero/negative totals; output exactly {"label": str,"quantity": int}
sorted by Python string ordering. Reject more than max_rows data records or
max_labels distinct normalized labels. Limits must positive integers, not bool.
Do not expose partial results on failure. Keep memory bounded by distinct labels.

## Durable job module: jobs.py

Expose Store(path, max_pending=10000), with methods:
- submit(key, kind, payload)->dict. All are strings. key fullmatches
  ASCII [A-Za-z0-9_-]{1,80}; kind fullmatches [a-z][a-z0-9_]{0,31}; payload is a
  lowercase SHA-256 digest [0-9a-f]{64}. Invalid arguments raise ValueError.
  Same key+kind+payload always returns the same job unchanged. Same key with
  different kind or payload raises ValueError('idempotency conflict'). Atomic across
  independent processes. New work beyond max_pending queued/running jobs raises
  OverflowError; duplicate lookup still succeeds at capacity. No database connection
  remains held by the object. Initialize schema safely, WAL and busy timeout.
- get(job_id)->dict or None. Returned public records have exactly id,key,kind,payload,
  status,attempts,token,lease_until,result,error. id is an opaque nonempty string;
  statuses queued/running/succeeded/failed; attempts is integer starting 0; token,
  lease_until,result,error initially None. result is JSON-compatible on success;
  error is string on failure. get is read-only. Unknown IDs return None.
- claim(now, ttl=30.0)->dict or None. now finite >=0, ttl finite >0; booleans and
  nonnumeric inputs invalid. One atomic transaction claims the oldest eligible job
  (submission order): queued or running with lease_until<=now. Increment attempts,
  assign a fresh opaque token, set lease_until=now+ttl and status running. Concurrent
  claimers never share ownership. At most 3 attempts per job. Expired running jobs
  with attempts>=3 become failed with a nonempty error and cleared token/lease.
- finish(job_id, token, now, *, result=None, error=None)->bool. Validate finite now.
  Require exactly one of non-None result or non-None error; result JSON must reject
  NaN/Infinity and encode to <=1MiB UTF-8. error must nonempty str <=2000 chars.
  Only current running token with lease_until>now may publish. Stale/expired token,
  duplicate completion or unknown job returns False and changes nothing. On success
  atomically store result/error, status succeeded/failed, clear token/lease and
  return True. Publishing result once is the only business side effect; no external
  side effects or global inventory table. Errors are terminal; abandoned work retries
  by lease expiry. Submission/claim/finish use short transactions with rollback and
  no handler execution inside a transaction.

path str/Path parent exists. max_pending positive integer not bool. Results/payload
IDs are durable across independent Store objects and process restarts. Do not add
CSV-specific methods or abstract backend classes: storage implementation is hidden
behind these four concrete operations and can later be replaced as one module.

## Worker module: worker.py

Expose run_once(store, blob_root, handlers, *, now=None, ttl=30.0)->bool. handlers
maps kind strings to callables taking an open binary stream and returning a JSON
result. Claim one job with time.time() unless explicit now is supplied; return False
if none. Open its immutable payload with blobs.open_blob in a with block, invoke
handler, then finish result; return True whenever work was claimed. Catch handler/
read errors and finish a bounded nonempty error, not a traceback. Unknown kind fails
that job. Explicit now is a deterministic test clock: use it at claim and finish;
otherwise obtain a fresh wall-clock value at finish so expired work cannot publish.
Do not catch KeyboardInterrupt/SystemExit: abrupt termination leaves a lease that
can be reclaimed. Do not assume current worker still owns the lease after handling.

Expose csv_handler(stream) calling tabular.summarize via io.TextIOWrapper with
UTF-8 and newline=''. Expose main(argv=None)->int and python -m worker:
--db PATH --blobs PATH [--once] [--poll SECONDS]. Loop polls (default .2 seconds) or
processes at most one job and exits with --once. Built-in mapping is {'inventory_csv':
csv_handler}. Poll must finite >0; argument errors return 2, help returns 0. Catch
Ctrl-C gracefully in the command entry only. Command owns Store creation; run_once
accepts Store and handlers from callers. A second handler must work without editing
jobs.py or run_once. Output no payload contents or tracebacks for job failures.

## HTTP module: api.py

Expose create_app(db_path, blob_root, max_upload_bytes=67108864)->FastAPI and main
entry python -m api --db PATH --blobs PATH [--host 127.0.0.1] [--port 8000].
- GET /health returns 200 JSON {"status":"ok"}.
- POST /imports accepts raw streamed CSV bytes, with required Idempotency-Key header.
  Store bytes with blobs.put_blob, submit kind inventory_csv; return 202 public job
  JSON on new or matching duplicate. Missing/invalid key ->400, changed payload for
  existing key ->409, over-limit upload ->413, queue full ->429. Use request streaming
  with bounded temporary spooling rather than request.body()/whole-file reads. Close
  temporary resources on errors/disconnect. Failed submit may leave an immutable
  unreferenced blob; document offline retention/cleanup as operational follow-up.
- GET /imports/{job_id} ->200 public job record, unknown ->404.
- GET /imports/{job_id}/result ->200 JSON result only when succeeded; unknown ->404,
  other statuses ->409. No route executes job handlers; worker is a separate process.

Keep upload memory bounded and validate key before storing payload. Persistence comes
from Store. Runtime FastAPI and uvicorn are preinstalled. Use no network calls except
local serving. Input CSV validation happens asynchronously in the worker; upload of
invalid CSV still creates a job which later fails with row diagnostics.

## Packaging: pyproject.toml

Distribution importflow-local 0.1.0, Python >=3.11. setuptools.build_meta, build
requirements setuptools and wheel. Include five top-level modules blobs,tabular,jobs,
worker,api plus no extras. Runtime dependencies fastapi and uvicorn using the exact
provisioned versions listed in ENVIRONMENT.md. Console scripts importflow-api=api:main
and importflow-worker=worker:main. Offline --no-deps --no-build-isolation --target
installation must work. Sandbox writable folders are noexec; invoke installed scripts
via Python from outside source. Packaging checks need all implementation modules.

## Tests: tests/test_importflow.py

At least eight collected pytest cases using real implementation (parameterized cases
count). Cover CSV validation including newline/type/quote boundaries; blob streaming
and size rejection; submit idempotency/conflict; stale lease/reclaim; duplicate finish;
handler reuse; HTTP processing and errors. Tests must pass independent correct
reference behavior and fail these faults: parser always [], submit ignores duplicate
keys, finish always False. Keep tests concise; don't emit redundant repeated cases.
Declare implementation dependencies needed for each test task. No skip/xfail or fake
implementation imports.

## Documentation: README.md

Describe install, API/worker commands, curl upload/status/result examples, pytest,
limits, job states, duplicate semantics, stale-worker fencing, 3-attempt recovery,
SQLite single-host WAL and serialized writes, payload retention, and second-handler
reuse. Document scale path: shared payload storage and database adapter, bounded
workers and resource/load qualification. Do not claim unlimited or multi-host scale.
