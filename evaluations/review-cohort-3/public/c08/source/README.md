# Usage

Action match: choices is a list of lists of resource names (nonempty strings). Each outer entry is one job; resources can be assigned to at most one job. Return maximum number of jobs that can receive one of their listed resources. Duplicate choices do not change result. Empty jobs/choices are allowed. At most 30 jobs and 30 distinct resources.

Invoke the command using JSON on standard input. For example:

```sh
printf '%s\n' '{"action": "match", "choices": [["a", "b"], ["a"]]}' | python cli.py
```

The identity action remains available. Run regression tests with python -m unittest discover.
