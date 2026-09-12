Install dagorder: pip install .
CLI: dagorder input.txt
Python API: core.run(text)
Test: python -m pytest
Input format and ordering: Expose run(text: str)->list[str] in core.py. Parse JSON object mapping node
names to prerequisite lists. Names match ASCII [a-z][a-z0-9_]{0,31}. Every
prerequisite must name a key, and lists contain distinct names. Empty object yields
[]. Non-string input, malformed JSON, duplicate JSON object keys, non-object root,
invalid names, non-list values, non-string entries, duplicate prerequisites,
missing prerequisite keys, self-dependencies and cycles raise ValueError.
Return every node exactly once in topological order, prerequisites first. At EACH
step choose the lexicographically smallest currently available node (not whole
sorted layers). Example {"a":[],"b":["a"],"z":[]} -> ["a","b","z"]. Result
must be independent of object-key order and prerequisite-list order. No external
state, graph mutation, network or dynamic code execution.

Invalid input raises ValueError; CLI returns 2.
