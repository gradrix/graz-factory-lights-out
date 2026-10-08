# Existing JSON utility

Use `python cli.py` with one JSON object on stdin. Existing action: revision. Domain functions accept the payload object; api.dispatch routes it. CLI reports ValueError/KeyError with stderr and exit 2.

## New usage

Action migrate with document. Supported revision-1 schema: {revision:1,users:[{id:string,name:string,active:bool}],...extras}; revision-2 schema: {revision:2,users:[{id:string,profile:{name:string},enabled:bool}],...extras}; revision-3 schema: {revision:3,accounts:{id:{profile:{name:string},enabled:bool}},order:[IDs],...extras}. Convert revisions 1 or 2 to revision 3, preserving user order, exact names, flags and all unrelated top-level keys. User IDs must be unique or raise ValueError. Existing revision 3 must return a deep independent unchanged copy. Other revision numbers raise ValueError. Revision 1/2 inputs do not already contain accounts/order keys; all listed field types are valid and user records contain exactly the listed fields. Empty users produce accounts={} and order=[]. Remove users from migrated output. Preserve action revision. Migration must be idempotent and must not mutate inputs or share nested output containers with them.

Example:

```sh
printf '%s\n' '{"action": "migrate", "document": {"revision": 1, "title": "Team", "users": [{"id": "u1", "name": "Ann", "active": true}]}}' | python cli.py
```

Output:

```json
{"revision": 3, "title": "Team", "accounts": {"u1": {"profile": {"name": "Ann"}, "enabled": true}}, "order": ["u1"]}
```

Inputs that violate the rules above raise ValueError; the CLI then prints the message on stderr and exits with status 2. Run the regression tests with `python -m unittest discover`.
