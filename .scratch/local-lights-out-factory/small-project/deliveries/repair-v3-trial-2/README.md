# Taskdock

A small single-user local task manager. Python 3.11+, standard library only, offline.

## Installation

```bash
pip install .
```

## Usage

All commands require `--file PATH` before the subcommand.

### Add a task

```bash
python -m taskdock_cli --file tasks.json add "Buy groceries"
```

Prints the created task as JSON.

### List tasks

```bash
python -m taskdock_cli --file tasks.json list
```

Prints active (non-completed) tasks as a JSON array. Use `--all` to include completed tasks.

### Complete a task

```bash
python -m taskdock_cli --file tasks.json done 1
```

Prints the completed task as JSON.

### Export as Markdown

```bash
python -m taskdock_cli --file tasks.json export
```

Prints a Markdown checklist of all tasks.

## Storage

Tasks are stored as a UTF-8 JSON file with the structure:

```json
{"version": 1, "tasks": [{"id": 1, "title": "...", "done": false}]}
```

A missing file represents an empty task list. Reading or listing never creates the file.

## Limitations

- Single-writer only; concurrent writers are not supported.
- No network, credentials, or production data.
- No deletion of tasks.

## Testing

```bash
pytest
```
