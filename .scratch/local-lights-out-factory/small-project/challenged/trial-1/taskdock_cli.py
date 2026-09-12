import argparse
import json
import sys

import taskdock


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="taskdock", description="Local task manager")
    parser.add_argument("--file", required=True, help="Path to storage file")
    sub = parser.add_subparsers(dest="command")

    add_p = sub.add_parser("add", help="Add a task")
    add_p.add_argument("title", help="Task title")

    list_p = sub.add_parser("list", help="List tasks")
    list_p.add_argument("--all", action="store_true", help="Include completed tasks")

    done_p = sub.add_parser("done", help="Complete a task")
    done_p.add_argument("id", type=int, help="Task ID")

    sub.add_parser("export", help="Export tasks as markdown")

    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        if e.code == 0:
            return 0
        return 2

    if args.command is None:
        print("error: a command is required", file=sys.stderr)
        return 2

    try:
        if args.command == "add":
            task = taskdock.add_task(args.file, args.title)
            print(json.dumps(task))
        elif args.command == "list":
            tasks = taskdock.list_tasks(args.file, include_done=args.all)
            print(json.dumps(tasks))
        elif args.command == "done":
            task = taskdock.complete_task(args.file, args.id)
            print(json.dumps(task))
        elif args.command == "export":
            sys.stdout.write(taskdock.export_markdown(args.file))
        else:
            print("error: unknown command", file=sys.stderr)
            return 2
    except (ValueError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
