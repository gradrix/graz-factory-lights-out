# Service readiness summary

Existing action check_names is exposed through api.dispatch and python cli.py, accepting one JSON object on stdin and writing one JSON result.

Add action readiness with required:list of unique service names, checks:list of {service:string,state:one of up/down/unknown,critical:boolean}, and quorum:integer 0..100. Up to 100 required names and 200 checks. For each service mentioned in required or checks, use ONLY its LAST check; missing required services count unknown and noncritical. Return {ready:boolean,up:integer,blockers:[service names]}. up counts distinct services whose last state is up, including services not required. blockers includes every required service whose last state is not up or missing, plus every service whose last check is critical and not up. Deduplicate blockers and sort by Python string order. ready is true exactly when up>=quorum and blockers is empty. Earlier critical flags have no effect once replaced. Empty inputs with quorum 0 is ready.

Example (SQLite requires the documented database to already exist):

```sh
printf '%s\n' '{"action": "readiness", "required": ["db"], "checks": [{"service": "db", "state": "up", "critical": true}, {"service": "web", "state": "up", "critical": false}], "quorum": 2}' | python cli.py
```

Run tests with python -m unittest discover. Inputs remain unchanged and failures follow the documented CLI error contract.
