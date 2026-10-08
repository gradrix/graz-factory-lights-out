# Existing JSON utility

Use `python cli.py` with one JSON object on stdin. Existing action: labels. Domain functions accept the payload object; api.dispatch routes it. CLI reports ValueError/KeyError with stderr and exit 2.

## New usage

Action order with nodes: a list of objects {id: nonempty string, deps: list of IDs}. IDs must be unique, every dependency must name an input node; unknown dependency or duplicate ID raises ValueError. Repeated dependency entries are treated as one edge. Return a list of all IDs in topological order. At EACH selection choose the earliest node in the original nodes list among currently eligible nodes; newly eligible earlier nodes outrank later nodes already eligible. A cycle (including self-dependency) raises ValueError. Empty nodes returns []. Preserve action labels and its input-order behavior. All shapes/types are valid as described; only the explicit duplicate/unknown/cycle errors need validation.

Example:

```sh
printf '%s\n' '{"action": "order", "nodes": [{"id": "app", "deps": ["lib"]}, {"id": "lib", "deps": []}]}' | python cli.py
```

Output:

```json
["lib", "app"]
```

Inputs that violate the rules above raise ValueError; the CLI then prints the message on stderr and exits with status 2. Run the regression tests with `python -m unittest discover`.
