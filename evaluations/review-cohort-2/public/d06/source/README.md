# Daily backup retention plan

Existing action backup_ids is exposed through api.dispatch and python cli.py, accepting one JSON object on stdin and writing one JSON result.

Add action plan with backups: list of {id:unique nonempty string,service:nonempty string,finished:UTC timestamp exactly YYYY-MM-DDTHH:MM:SSZ}, and days: integer 0..30. Inputs have valid calendar timestamps in 2000..2090, at most 200 backups. For EACH service retain only the latest backup on each of its newest days distinct UTC calendar dates. If backups on one date have identical finished timestamps, retain the smallest id in Python string order. Return {keep:[ids],delete:[ids]}, both lists in original backup input order. days=0 deletes all. Different services have separate retention counts. This is a preview only and must not access files.

Example (SQLite requires the documented database to already exist):

```sh
printf '%s\n' '{"action": "plan", "backups": [{"id": "old", "service": "db", "finished": "2026-01-01T10:00:00Z"}, {"id": "early", "service": "db", "finished": "2026-01-02T10:00:00Z"}, {"id": "late", "service": "db", "finished": "2026-01-02T11:00:00Z"}, {"id": "web", "service": "web", "finished": "2025-12-01T00:00:00Z"}], "days": 1}' | python cli.py
```

Run tests with python -m unittest discover. Inputs remain unchanged and failures follow the documented CLI error contract.
