"""Trusted preflight reference CLI."""

import argparse
import json
import sys

import taskdock


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("add").add_argument("title")
    sub.add_parser("list").add_argument("--all", action="store_true")
    sub.add_parser("done").add_argument("id", type=int)
    sub.add_parser("export")
    try:
        args = parser.parse_args(argv)
        if args.command == "add":
            result = taskdock.add_task(args.file, args.title)
        elif args.command == "list":
            result = taskdock.list_tasks(args.file, args.all)
        elif args.command == "done":
            result = taskdock.complete_task(args.file, args.id)
        else:
            print(taskdock.export_markdown(args.file), end="")
            return 0
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (ValueError, OSError) as error:
        print("error: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
