import argparse
import json
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="dagorder",
        description="Topological sort of a JSON dependency graph.",
    )
    parser.add_argument("path", help="path to UTF-8 JSON input file")
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        # argparse exits 0 for --help, 2 for errors; return that status
        return int(e.code) if e.code is not None else 0

    try:
        with open(args.path, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError:
        sys.stderr.write(f"error: cannot read file {args.path!r}\n")
        return 2

    try:
        result = _core_run(text)
    except ValueError as e:
        sys.stderr.write(f"error: {e}\n")
        return 2
    except Exception as e:
        sys.stderr.write(f"error: {e}\n")
        return 2

    sys.stdout.write(json.dumps(result) + "\n")
    return 0


def _core_run(text: str) -> list[str]:
    from core import run
    return run(text)


if __name__ == "__main__":
    sys.exit(main())
