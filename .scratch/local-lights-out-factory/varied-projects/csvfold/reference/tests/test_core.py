import pytest
import core

def test_valid_0():
    assert core.run('label,quantity\n') == []

def test_valid_1():
    assert core.run('label,quantity\nz,1\na,2\nz,-1\n') == [{'label': 'a', 'quantity': 2}, {'label': 'z', 'quantity': 0}]

def test_valid_2():
    assert core.run('label,quantity\r\n" café,blue ",+03\r\n') == [{'label': 'café,blue', 'quantity': 3}]

def test_invalid_0():
    with pytest.raises(ValueError):
        core.run('')

def test_invalid_1():
    with pytest.raises(ValueError):
        core.run('label\n')

def test_invalid_2():
    with pytest.raises(ValueError):
        core.run('quantity,label\n')

def test_invalid_3():
    with pytest.raises(ValueError):
        core.run('label,quantity,quantity\n')

def test_invalid_4():
    with pytest.raises(ValueError):
        core.run('label,quantity\n\n')

def test_invalid_5():
    with pytest.raises(ValueError):
        core.run('label,quantity\na\n')

def test_invalid_6():
    with pytest.raises(ValueError):
        core.run('label,quantity\na,1,x\n')

def test_invalid_7():
    with pytest.raises(ValueError):
        core.run('label,quantity\n ,1\n')

def test_invalid_8():
    with pytest.raises(ValueError):
        core.run('label,quantity\n"\na",1\n')

def test_invalid_9():
    with pytest.raises(ValueError):
        core.run('label,quantity\na,1.0\n')

def test_invalid_10():
    with pytest.raises(ValueError):
        core.run('label,quantity\na, 1\n')

def test_invalid_11():
    with pytest.raises(ValueError):
        core.run('label,quantity\na,١\n')

def test_invalid_12():
    with pytest.raises(ValueError):
        core.run('label,quantity\n"unterminated,1\n')

