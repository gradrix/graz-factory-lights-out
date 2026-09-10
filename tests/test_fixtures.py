"""Trusted example generation rejects incorrect or ambiguous expected values."""

import importlib.util
from pathlib import Path

import pytest

from gflo.fixtures import Example, verify_examples


def test_verified_examples_reject_wrong_and_bool_integer_confusion():
    example = Example(name="draw", inputs={"x": 1}, expected={"possible": False})
    with pytest.raises(ValueError, match="rejected"):
        verify_examples((example,), producer_digest="a" * 64, oracle=lambda _: {"possible": 0})
    result = verify_examples(
        (example,), producer_digest="a" * 64, oracle=lambda _: {"possible": False}
    )
    assert result.examples == (example,)


def test_game_examples_have_independently_checked_draw_and_wins():
    spec = importlib.util.spec_from_file_location(
        "game_examples", Path(__file__).parents[1] / "scripts/prepare_game_rule_examples.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.produce()
    assert [e.name for e in result.examples] == ["empty", "full-draw", "already-winning"]
    draw = result.examples[1].inputs["board"]
    assert all(0 not in row and len(set(row)) == 2 for row in draw)
    assert all(len({draw[y][x] for y in range(3)}) == 2 for x in range(3))
    assert len({draw[i][i] for i in range(3)}) == 2
    assert len({draw[i][2 - i] for i in range(3)}) == 2
