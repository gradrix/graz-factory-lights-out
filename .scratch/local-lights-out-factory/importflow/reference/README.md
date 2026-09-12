# Importflow reference for gate qualification

Install: `pip install .`; tests: `python -m pytest`.
API: `python -m api --db jobs.db --blobs payloads`.
Worker: `python -m worker --db jobs.db --blobs payloads`.
Upload: `curl -H 'Idempotency-Key: batch-1' --data-binary @input.csv localhost:8000/imports`.
Status: `curl localhost:8000/imports/ID`. Result: `curl localhost:8000/imports/ID/result`.
CSV header label,quantity; invalid values produce row diagnostics.
Limits: 64 MiB upload, 1,000,000 rows, 1,000 labels; bounded streaming memory.
Jobs move queued -> running -> succeeded or failed. Idempotency keys deduplicate the
same content and reject conflicts. Expiring leases fence stale workers; 3 attempts
maximum recover abandoned jobs. Results publish once in a transaction. Long jobs
that exceed the lease cannot publish; choose a measured lease duration for the load.
SQLite WAL supports multiple processes on one host with serialized writes. Multi-host
scale requires shared payload storage and another database adapter plus load checks.
Blobs are immutable and retained; failed submissions can leave unreferenced payloads.
Offline retention/cleanup is operational follow-up. Reuse workers with a second
handler by adding a kind->callable mapping without editing durable job storage.
