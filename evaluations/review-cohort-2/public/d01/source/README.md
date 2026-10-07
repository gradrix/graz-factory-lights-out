# Contact import preview

Existing action emails is exposed through api.dispatch and python cli.py, accepting one JSON object on stdin and writing one JSON result.

Add action import_contacts with csv: a string of valid CSV syntax, up to 200 rows and 10000 code points, and existing: a list of contact objects {email,name}. Existing email strings are already unique normalized lowercase ASCII. Parse comma-separated CSV with the standard double-quote quoting convention. The header must be exactly email,name in that order; each subsequent record must have exactly two columns. A contact email after stripping surrounding whitespace and lowercasing must have exactly one @, nonempty parts on both sides, and no whitespace anywhere. A stripped name must be nonempty. Invalid header, column count, email or name raises ValueError. Deduplicate new email addresses after normalization: retain their first CSV occurrence, then discard those already present in existing. Return {added:[{email,name},...], skipped:integer}; skipped counts every valid CSV data record not added (including repeat occurrences). Validate every record, even duplicates that would be skipped. Do not change existing. A header-only CSV is valid; an empty string is invalid. Embedded quoted newlines in names are allowed.

Example (SQLite requires the documented database to already exist):

```sh
printf '%s\n' '{"action": "import_contacts", "csv": "email,name\n A@X , Ada \na@x,Ignored\nb@x,\"Bee, Two\"\n", "existing": []}' | python cli.py
```

Run tests with python -m unittest discover. Inputs remain unchanged and failures follow the documented CLI error contract.
