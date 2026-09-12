import core
valid = [('label,quantity\n', []), ('label,quantity\nz,1\na,2\nz,-1\n', [{'label': 'a', 'quantity': 2}, {'label': 'z', 'quantity': 0}]), ('label,quantity\r\n" café,blue ",+03\r\n', [{'label': 'café,blue', 'quantity': 3}])]
invalid = [None, 1, True, '', 'label\n', 'quantity,label\n', 'label,quantity,quantity\n', 'label,quantity\n\n', 'label,quantity\na\n', 'label,quantity\na,1,x\n', 'label,quantity\n ,1\n', 'label,quantity\n"\na",1\n', 'label,quantity\na,1.0\n', 'label,quantity\na, 1\n', 'label,quantity\na,١\n', 'label,quantity\n"unterminated,1\n']
for raw, expected in valid:
    actual = core.run(raw)
    assert actual == expected, (raw, expected, actual)
for raw in invalid:
    try:
        core.run(raw)
    except ValueError:
        pass
    else:
        raise AssertionError(('invalid accepted', raw))
print('api-ok')
