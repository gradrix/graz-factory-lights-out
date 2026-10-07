# HTTP access report

Existing action routes is exposed through api.dispatch and python cli.py, accepting one JSON object on stdin and writing one JSON result.

Add action report with entries: list of {route:string,status:integer 100..599,ms:nonnegative integer}, and min_requests: integer 1..200. At most 200 entries, route strings 1..100 code points. Group by exact route. Return a list sorted by route in Python string order; omit groups with fewer than min_requests entries. Each row is {route,requests,errors,p95_ms}. Errors count status >=500. The p95 is nearest rank: sort milliseconds ascending and choose the ceil(0.95*n)-th value counting from one. Never round an averaged percentile. Empty entries yields [].

Example (SQLite requires the documented database to already exist):

```sh
printf '%s\n' '{"action": "report", "entries": [{"route": "/b", "status": 503, "ms": 90}, {"route": "/a", "status": 404, "ms": 0}, {"route": "/b", "status": 200, "ms": 10}], "min_requests": 1}' | python cli.py
```

Run tests with python -m unittest discover. Inputs remain unchanged and failures follow the documented CLI error contract.
