# log_summary

Summarize JSON Lines logs with a small standard-library CLI.

## Usage

```
python log_summary.py PATH [--strict]
```

- `PATH` — log file, or `-` to read from stdin.
- Each nonblank line must be a JSON object with nonempty string fields
  `service` and `level`. `service` is whitespace-trimmed; `level` is
  trimmed and uppercased. Any nonempty level name is accepted.
- Blank lines are ignored entirely.
- Default mode: invalid records are skipped and counted in `invalid`.
- `--strict`: stop on the first invalid record, exit code 2, print a
  line-number error to stderr, and print nothing on stdout.
- Missing/unreadable files: exit code 2 with a clear stderr message.

## Output

One JSON object on stdout:

```json
{"total": <valid_count>, "invalid": <invalid_count>,
 "by_service": {"<service>": <count>, ...},
 "by_level": {"<LEVEL>": <count>, ...}}
```

## Examples

```sh
$ printf '{"service":" alpha ","level":" info "}\nnot json\n{"service":"beta","level":"warn"}\n' > log.jsonl
$ python log_summary.py log.jsonl
{"total": 2, "invalid": 1, "by_service": {"alpha": 1, "beta": 1}, "by_level": {"INFO": 1, "WARN": 1}}

$ cat log.jsonl | python log_summary.py -
{"total": 2, "invalid": 1, "by_service": {"alpha": 1, "beta": 1}, "by_level": {"INFO": 1, "WARN": 1}}

$ python log_summary.py --strict log.jsonl
error: invalid record on line 2: not valid JSON
$ echo $?
2
```

## Tests

```sh
python -m unittest discover -s tests -v
```
