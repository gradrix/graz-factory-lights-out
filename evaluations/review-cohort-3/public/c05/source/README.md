# Usage

Action wrap: text is a string up to 2000 Unicode code points, width is integer 1..80. Split text into paragraphs on literal newline, preserving empty paragraphs. Within each paragraph split on whitespace, collapse separators to one ASCII space, greedily place words on lines no longer than width. A word longer than width occupies its own line intact. Return list of lines. Each empty/whitespace-only paragraph contributes one empty string. Width measures Python len.

Invoke the command using JSON on standard input. For example:

```sh
printf '%s\n' '{"action": "wrap", "text": "one two three", "width": 7}' | python cli.py
```

The identity action remains available. Run regression tests with python -m unittest discover.
