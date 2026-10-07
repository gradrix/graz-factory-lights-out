# Release digest builder

Existing action change_ids is exposed through api.dispatch and python cli.py, accepting one JSON object on stdin and writing one JSON result.

Add action digest with changes: list of {id:nonempty string,category:one of added/fixed/removed,title:string,internal:boolean}, up to 200 rows. First deduplicate all rows by id, retaining the LAST occurrence and its position. Then omit retained internal rows. Return a Markdown string containing nonempty category sections in fixed order added, fixed, removed, headed exactly ## Added / ## Fixed / ## Removed. Within a section retain surviving last-occurrence order. A bullet is "- " plus title with each run of whitespace replaced by one ASCII space and leading/trailing whitespace stripped. Separate sections by one blank line, finish any nonempty output with one newline; no changes returns empty string. Titles may contain Markdown punctuation, which is preserved literally; no escaping is requested.

Example (SQLite requires the documented database to already exist):

```sh
printf '%s\n' '{"action": "digest", "changes": [{"id": "1", "category": "fixed", "title": " A\n fix ", "internal": false}, {"id": "2", "category": "added", "title": "New **API**", "internal": false}]}' | python cli.py
```

Run tests with python -m unittest discover. Inputs remain unchanged and failures follow the documented CLI error contract.
