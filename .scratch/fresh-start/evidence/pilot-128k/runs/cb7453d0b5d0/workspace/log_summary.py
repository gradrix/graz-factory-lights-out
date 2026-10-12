#!/usr/bin/env python3
"""Summarize JSON Lines logs.

Usage: python log_summary.py PATH [--strict]
       PATH may be '-' to read from stdin.
"""
import argparse
import json
import sys


def validate_record(obj):
    """Return (service, level) for a valid record, or None if invalid.

    A record is valid when obj is a dict with string "service" and
    string "level" that are nonempty after trimming (level is also
    uppercased).
    """
    if not isinstance(obj, dict):
        return None
    service = obj.get("service")
    level = obj.get("level")
    if not isinstance(service, str) or not isinstance(level, str):
        return None
    service = service.strip()
    level = level.strip().upper()
    if not service or not level:
        return None
    return service, level


def summarize(lines, strict=False):
    """Consume an iterable of raw lines and return the summary dict.

    Blank lines are ignored entirely. Invalid records are counted in
    "invalid" unless strict=True, in which case a ValueError with an
    explanatory message naming the line number is raised on the first
    invalid record.
    """
    total = 0
    invalid = 0
    by_service = {}
    by_level = {}
    for lineno, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line:
            continue  # blank lines are ignored entirely
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            if strict:
                raise ValueError(
                    "invalid record on line %d: not valid JSON" % lineno
                )
            invalid += 1
            continue
        result = validate_record(obj)
        if result is None:
            if strict:
                raise ValueError(
                    "invalid record on line %d: expected a JSON object "
                    "with nonempty string fields \"service\" and "
                    "\"level\"" % lineno
                )
            invalid += 1
            continue
        service, level = result
        total += 1
        by_service[service] = by_service.get(service, 0) + 1
        by_level[level] = by_level.get(level, 0) + 1
    return {
        "total": total,
        "invalid": invalid,
        "by_service": by_service,
        "by_level": by_level,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Summarize JSON Lines logs (one JSON object per line)."
    )
    parser.add_argument(
        "path",
        help='path to the log file, or "-" to read from stdin',
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="stop on the first invalid record (exit code 2)",
    )
    args = parser.parse_args(argv)

    try:
        if args.path == "-":
            summary = summarize(sys.stdin, strict=args.strict)
        else:
            with open(args.path, "r") as fh:
                summary = summarize(fh, strict=args.strict)
    except OSError as exc:
        print("error: cannot open %s: %s" % (args.path, exc), file=sys.stderr)
        return 2
    except ValueError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2

    json.dump(summary, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
