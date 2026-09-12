import core
valid = [('{}', []), ('{"z":[],"b":["a"],"a":[]}', ['a', 'b', 'z']), ('{"c":["a","b"],"b":[],"a":[]}', ['a', 'b', 'c'])]
invalid = [None, 1, True, '', '[]', '{"a":[],"a":[]}', '{"A":[]}', '{"a":{}}', '{"a":[true]}', '{"a":["b"]}', '{"a":["a"]}', '{"a":["b"],"b":["a"]}', '{"a":[],"b":["a","a"]}', '{"a":[],"b":[1]}']
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
