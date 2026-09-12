# Taskdock product brief

Create a small installable Python project for a single user managing local tasks.
Python 3.11+, standard library runtime only, offline, UTF-8. No service, network,
credentials or production data. Concurrent writers and deletion are out of scope.
The initial repository contains only this brief and an unrelated archive sentinel.
Create exactly taskdock.py, taskdock_cli.py, pyproject.toml, README.md and
tests/test_taskdock.py. Do not modify the brief or sentinel.

## Storage API — taskdock.py

Expose add_task(path, title) -> dict, list_tasks(path, include_done=False) -> list,
complete_task(path, task_id) -> dict, and export_markdown(path) -> str.
path accepts a str or pathlib.Path. Each task is exactly
{"id": positive integer, "title": trimmed string, "done": boolean}.
Storage is a UTF-8 JSON object {"version": 1, "tasks": [tasks]}.
A missing file represents an empty list. Reading/listing/exporting never creates it.
Add appends a new task with done false and id max(existing ids, default 0)+1;
completed tasks still reserve their IDs. Duplicate titles are permitted.
Titles must be strings, strip to 1–120 characters, and contain no CR or LF.
Invalid title input raises ValueError and leaves storage unchanged.
list_tasks returns ascending-ID tasks, excluding completed tasks by default; true
include_done includes all tasks. complete_task requires a positive int (not bool),
raises ValueError for invalid or unknown IDs, and persists done true. Completing an
already completed task succeeds idempotently. Functions return task dictionaries.
export_markdown includes all tasks sorted by ID. Its exact format is '# Tasks\n'
then one line per task: '- [ ] ID: TITLE\n' or '- [x] ID: TITLE\n'. Empty export is
just '# Tasks\n'. Preserve Unicode titles literally; Markdown escaping is not required.

Reject malformed JSON, invalid root/version/tasks, extra root or task keys,
nonpositive or duplicate task IDs, bool IDs, invalid stored titles (including
untrimmed ones), and nonboolean done values with ValueError. Version must be
integer 1, not bool. Never overwrite invalid storage. Storage ordering need not
be sorted; API outputs are sorted. Other filesystem errors may propagate as OSError.
Writes must use a temporary file in the destination directory and os.replace,
cleaning up temporary files on failure. Failure before replacement must preserve
existing bytes. Parent directories must already exist; do not create directories.

## CLI — taskdock_cli.py

Expose main(argv=None) -> int and support python -m taskdock_cli. Global --file PATH
is required before the subcommand. Commands:

- add TITLE: write a task and print the returned task as one JSON value plus newline.
- list [--all]: print the matching task array as one JSON value plus newline.
- done ID: complete the task and print the returned task as one JSON value plus newline.
- export: print exactly export_markdown's output, with no extra newline.

Successful commands exit 0. Invalid arguments, bad storage, unknown IDs and filesystem
failures exit 2, write an explanatory error to stderr, leave stdout empty, and show
no Python traceback. --help exits 0. CLI behavior must call the real storage API,
and separate subprocess invocations must see persisted tasks.

## Packaging — pyproject.toml

Use setuptools.build_meta with build requirements setuptools and wheel. Distribution
name taskdock-local, version 0.1.0, Python >=3.11, no runtime dependencies. Include
both top-level modules using setuptools py-modules. Console script taskdock points
to taskdock_cli:main. Offline pip install --no-deps --no-build-isolation --target DIR .
must work in the supplied environment, with the installed entry script usable via
python DIR/bin/taskdock from outside the source directory using DIR on PYTHONPATH.
The sandbox's writable directories are noexec; direct OS launch is not part of this
qualification. Packaging work needs
both modules available for its checks; declare those dependencies in the plan.

## Tests and documentation

Create at least six substantive pytest test cases in tests/test_taskdock.py using
temporary paths and the real API. Cover persistence, completed filtering, monotonic
IDs after completion, invalid titles, invalid/corrupt storage preservation, and
idempotent completion/unknown-ID rejection. Generated tests must pass correct code
and fail implementations with broken done filtering, ID allocation, completion
persistence or title validation. No skips or replacement/fake implementation imports.
Test tasks need the storage implementation as a declared dependency.

README.md must explain installation, all four commands with --file examples,
running pytest, JSON storage, and the single-writer limitation. Use no absolute
machine-specific paths. CLI work depends on storage. The model may combine related
files into one bounded task; every produced file needs a producer in its plan.
