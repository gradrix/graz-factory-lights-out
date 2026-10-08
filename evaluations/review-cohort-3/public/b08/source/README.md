# Existing JSON utility

Use `python cli.py` with one JSON object on stdin. Existing action: ids. Domain functions accept the payload object; api.dispatch routes it. CLI reports ValueError/KeyError with stderr and exit 2.

## New usage

Action group with requested (list of unique string IDs in desired order) and responses (list of {id:string,ok:bool,value:JSON} when ok=true or {id:string,ok:false,error:string}). For each requested ID, exactly zero or one response is allowed. Reject duplicate requested IDs, unknown response IDs or duplicate responses with ValueError. Return {successes:[{id,value}],failures:[{id,error}],missing:[IDs]}. Every array follows requested order, independent of response arrival order. Missing IDs appear only in missing; falsey successful values (null,false,0,empty string) remain successes. No request is retried or synthesized. Preserve action ids. Shapes/types match this contract.

Example:

```sh
printf '%s\n' '{"action": "group", "requested": ["a", "b", "c"], "responses": [{"id": "c", "ok": false, "error": "timeout"}, {"id": "a", "ok": true, "value": 0}]}' | python cli.py
```

Output:

```json
{"successes": [{"id": "a", "value": 0}], "failures": [{"id": "c", "error": "timeout"}], "missing": ["b"]}
```

Inputs that violate the rules above raise ValueError; the CLI then prints the message on stderr and exits with status 2. Run the regression tests with `python -m unittest discover`.
