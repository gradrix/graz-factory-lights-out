#!/usr/bin/env python3
"""Produce bounded TicTacToe examples independently of the target implementation."""

import argparse
import hashlib
import itertools
from pathlib import Path

from gflo.fixtures import Example, verify_examples


def oracle(inputs):
    board = inputs["board"]
    lines = list(board) + [list(col) for col in zip(*board)]
    lines += [[board[i][i] for i in range(3)], [board[i][2 - i] for i in range(3)]]
    winners = sorted({line[0] for line in lines if line[0] != 0 and len(set(line)) == 1})
    possible = any(set(line) <= {0, figure} for line in lines for figure in (1, 2))
    return {"winners": winners, "possible": possible}


def produce():
    draw = next(
        [list(cells[i : i + 3]) for i in (0, 3, 6)]
        for cells in itertools.product((1, 2), repeat=9)
        if not oracle({"board": [list(cells[i : i + 3]) for i in (0, 3, 6)]})["winners"]
    )
    examples = (
        Example(
            name="empty",
            inputs={"board": [[0] * 3 for _ in range(3)]},
            expected={"winners": [], "possible": True},
        ),
        Example(
            name="full-draw", inputs={"board": draw}, expected={"winners": [], "possible": False}
        ),
        Example(
            name="already-winning",
            inputs={"board": [[0, 1, 2], [0, 1, 2], [1, 1, 1]]},
            expected={"winners": [1], "possible": True},
        ),
    )
    return verify_examples(
        examples,
        producer_digest=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        oracle=oracle,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(produce().canonical() + "\n")
