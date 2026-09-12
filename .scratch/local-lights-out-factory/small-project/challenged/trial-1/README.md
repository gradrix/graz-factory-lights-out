# Taskdock

A small local task manager for a single user. Python 3.11+, standard library only, offline.

## Installation

```bash
pip install .
```

## Usage

All commands require `--file PATH` before the subcommand.

### Add a task

```bash
python -m taskdock_cli --file tasks.json add "Write report"
```

Prints the created task as JSON.

### List tasks

```bash
python -m taskdock_cli --file tasks.json list
python -m taskdock_cli --file tasks.json list --all
```

Prints matching tasks as a JSON array. `--all` includes completed tasks.

### Complete a task

```bash
python -m taskdock_cli --file tasks.json done 1
```

Prints the completed task as JSON.

### Export as Markdown

```bash
python -m taskdock_cli --file tasks.json export
```

Prints all tasks in Markdown format.

## Storage

Tasks are stored as a UTF-8 JSON file with the structure:

```json
{"version": 1, "tasks": [{"id": 1, "title": "...", "done": false}]}
```

A missing file represents an empty task list. Reading, listing, and exporting never create the file.

## Limitations

- Single-writer only; concurrent writers are not supported.
- No deletion of tasks.
- No network access or credentials.

## Testing

```bash
pytest
```
