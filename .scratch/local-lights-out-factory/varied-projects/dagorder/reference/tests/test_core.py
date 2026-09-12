import pytest
import core

def test_valid_0():
    assert core.run('{}') == []

def test_valid_1():
    assert core.run('{"z":[],"b":["a"],"a":[]}') == ['a', 'b', 'z']

def test_valid_2():
    assert core.run('{"c":["a","b"],"b":[],"a":[]}') == ['a', 'b', 'c']

def test_invalid_0():
    with pytest.raises(ValueError):
        core.run('')

def test_invalid_1():
    with pytest.raises(ValueError):
        core.run('[]')

def test_invalid_2():
    with pytest.raises(ValueError):
        core.run('{"a":[],"a":[]}')

def test_invalid_3():
    with pytest.raises(ValueError):
        core.run('{"A":[]}')

def test_invalid_4():
    with pytest.raises(ValueError):
        core.run('{"a":{}}')

def test_invalid_5():
    with pytest.raises(ValueError):
        core.run('{"a":[true]}')

def test_invalid_6():
    with pytest.raises(ValueError):
        core.run('{"a":["b"]}')

def test_invalid_7():
    with pytest.raises(ValueError):
        core.run('{"a":["a"]}')

def test_invalid_8():
    with pytest.raises(ValueError):
        core.run('{"a":["b"],"b":["a"]}')

def test_invalid_9():
    with pytest.raises(ValueError):
        core.run('{"a":[],"b":["a","a"]}')

def test_invalid_10():
    with pytest.raises(ValueError):
        core.run('{"a":[],"b":[1]}')

