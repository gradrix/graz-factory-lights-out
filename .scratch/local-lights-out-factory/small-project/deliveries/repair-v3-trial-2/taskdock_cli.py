import argparse
import json
import sys

import taskdock


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="taskdock_cli")
    parser.add_argument("--file", required=True, help="Path to the storage file")
    sub = parser.add_subparsers(dest="command")

    add_p = sub.add_parser("add")
    add_p.add_argument("title")

    list_p = sub.add_parser("list")
    list_p.add_argument("--all", action="store_true")

    done_p = sub.add_parser("done")
    done_p.add_argument("id", type=int)

    sub.add_parser("export")

    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        # argparse already wrote to stderr for errors; exit 2 for invalid args
        if exc.code == 0:
            return 0
        return 2

    try:
        if args.command == "add":
            task = taskdock.add_task(args.file, args.title)
            sys.stdout.write(json.dumps(task) + "\n")
        elif args.command == "list":
            tasks = taskdock.list_tasks(args.file, include_done=args.all)
            sys.stdout.write(json.dumps(tasks) + "\n")
        elif args.command == "done":
            task = taskdock.complete_task(args.file, args.id)
            sys.stdout.write(json.dumps(task) + "\n")
        elif args.command == "export":
            sys.stdout.write(taskdock.export_markdown(args.file))
        else:
            parser.error("unknown command")
            return 2
    except ValueError as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2
    except OSError as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
