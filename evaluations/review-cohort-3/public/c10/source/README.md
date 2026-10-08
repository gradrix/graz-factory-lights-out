# Usage

Action tally: candidates is a list of unique nonempty string names. ballots is a list of lists of candidate names; an individual ballot approves each named candidate once despite repetitions. Unknown names anywhere raise ValueError. Return list of {candidate:name,votes:count}, descending votes then original candidate order. Include candidates with zero votes. Empty inputs allowed, <=100 candidates and <=1000 ballots.

Invoke the command using JSON on standard input. For example:

```sh
printf '%s\n' '{"action": "tally", "candidates": ["b", "a", "c"], "ballots": [["a", "a"], ["b"], []]}' | python cli.py
```

The identity action remains available. Run regression tests with python -m unittest discover.
