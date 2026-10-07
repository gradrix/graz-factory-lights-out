# Markdown heading catalog

Existing action line_count is exposed through api.dispatch and python cli.py, accepting one JSON object on stdin and writing one JSON result.

Add action headings with markdown:string <=10000 code points. Process splitlines() lines in order, line numbers start at one. A fence is any line whose stripped text starts with three backticks; each such line toggles fenced mode and is excluded, regardless of remaining text. Exclude all lines in fenced mode. Outside fences, recognize only lines beginning at column zero with 1..6 # characters followed by one ASCII space. The heading text is the remainder after that one space, stripped at both ends; trailing # are ordinary text. Return [{level:integer,text:string,line:integer,anchor:string}]. Anchor base: lowercase text, keep only ASCII a-z/0-9 and ASCII spaces/hyphens, replace each run of spaces/hyphens with one hyphen, trim hyphens. Empty base becomes "section". Ensure anchors are unique globally in order: use base if unused; otherwise try base-2, base-3, etc until unused, including collisions with earlier literal bases. Do not modify markdown.

Example (SQLite requires the documented database to already exist):

```sh
printf '%s\n' '{"action": "headings", "markdown": "# Hello World\ntext\n## Hello World\n"}' | python cli.py
```

Run tests with python -m unittest discover. Inputs remain unchanged and failures follow the documented CLI error contract.
