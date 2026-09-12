# Taskdock

Install with `pip install .`. Runtime uses Python's standard library.

```sh
taskdock --file tasks.json add "Read a book"
taskdock --file tasks.json list
taskdock --file tasks.json done 1
taskdock --file tasks.json list --all
taskdock --file tasks.json export
python -m pytest
```

Tasks persist in a local UTF-8 JSON file. Use a single writer; concurrent writers
are unsupported. `python -m taskdock_cli` is also available from the source tree.
