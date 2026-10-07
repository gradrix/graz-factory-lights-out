# Environment template renderer

Existing action variable_names is exposed through api.dispatch and python cli.py, accepting one JSON object on stdin and writing one JSON result.

Add action render with template: string <=4000 code points, variables: object mapping names to string values (<=100 names, values <=1000 code points). Names match ASCII [A-Za-z_][A-Za-z0-9_]*. Scan template left to right: $$ emits one literal dollar; ${NAME} substitutes its variable; any other dollar, malformed name, missing closing brace or undefined variable raises ValueError. A single-pass substitution is required: dollar text inside a variable value is literal and is never expanded. Text outside substitutions is preserved exactly, including newlines. Return rendered string. Empty template is valid. Escaped dollars consume two characters, so $${X} yields literal ${X}.

Example (SQLite requires the documented database to already exist):

```sh
printf '%s\n' '{"action": "render", "template": "host=${HOST}\nport=${PORT}", "variables": {"HOST": "example", "PORT": "443"}}' | python cli.py
```

Run tests with python -m unittest discover. Inputs remain unchanged and failures follow the documented CLI error contract.
