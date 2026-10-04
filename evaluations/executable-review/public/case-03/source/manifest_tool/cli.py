"""Command line interface (requirement A5)."""
import json
import sys
from .api import run


def main():
    """Read one JSON document on stdin, print the JSON result on stdout.

    On malformed JSON or an invalid action/payload, print exactly
    {"error": "invalid input"} and exit with status 2 (no traceback).
    """
    try:
        payload = json.load(sys.stdin)
        result = run(payload)
    except (ValueError, TypeError, RecursionError):
        print(json.dumps({'error': 'invalid input'}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0
