import json
import pytest

from core import run


def test_valid_ordering():
    assert run('{"a": [], "b": ["a"], "z": []}') == ["a", "b", "z"]


def test_empty_object():
    assert run('{}') == []


def test_non_string_input():
    with pytest.raises(ValueError):
        run(123)  # type: ignore[arg-type]


def test_malformed_json():
    with pytest.raises(ValueError):
        run('{invalid}')


def test_duplicate_json_keys():
    with pytest.raises(ValueError):
        run('{"a": [], "a": []}')


def test_non_object_root():
    with pytest.raises(ValueError):
        run('[1, 2, 3]')


def test_invalid_name():
    with pytest.raises(ValueError):
        run('{"A": []}')


def test_non_list_value():
    with pytest.raises(ValueError):
        run('{"a": "b"}')


def test_non_string_entry():
    with pytest.raises(ValueError):
        run('{"a": [1]}' )


def test_duplicate_prerequisites():
    with pytest.raises(ValueError):
        run('{"a": [], "b": ["a", "a"]}')


def test_missing_prerequisite_key():
    with pytest.raises(ValueError):
        run('{"a": ["x"]}')


def test_self_dependency():
    with pytest.raises(ValueError):
        run('{"a": ["a"]}')


def test_cycle():
    with pytest.raises(ValueError):
        run('{"a": ["b"], "b": ["a"]}')


def test_ordering_independent_of_key_order():
    r1 = run('{"a": [], "b": ["a"], "z": []}')
    r2 = run('{"z": [], "b": ["a"], "a": []}')
    assert r1 == r2 == ["a", "b", "z"]


def test_ordering_independent_of_prereq_order():
    r1 = run('{"a": [], "b": ["a"], "c": ["a", "b"]}')
    r2 = run('{"a": [], "b": ["a"], "c": ["b", "a"]}')
    assert r1 == r2 == ["a", "b", "c"]


def test_lexicographic_smallest_first():
    # a and z both available first; a is smaller
    assert run('{"a": [], "b": ["a"], "z": []}') == ["a", "b", "z"]


def test_complex_graph():
    # c depends on a and b; d depends on b; a and b available first
    assert run('{"a": [], "b": [], "c": ["a", "b"], "d": ["b"]}') == ["a", "b", "c", "d"]
