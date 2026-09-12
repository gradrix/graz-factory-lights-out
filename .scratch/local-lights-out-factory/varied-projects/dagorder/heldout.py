import json
import random
import core

rng = random.Random(5179)
for trial in range(50):
    names = list('abcdefghijk')
    rng.shuffle(names)
    graph = {node: [prior for prior in names[:i] if rng.random() < .25] for i, node in enumerate(names)}
    # Independent repeated scanning oracle, compared against permuted encodings.
    expected = []
    while len(expected) < len(names):
        for node in sorted(names):
            if node not in expected and all(d in expected for d in graph[node]):
                expected.append(node)
                break
    for _ in range(3):
        rng.shuffle(names)
        for deps in graph.values():
            rng.shuffle(deps)
        actual = core.run(json.dumps({n: graph[n] for n in names}))
        assert actual == expected, (trial, actual, expected)
for raw in ['{"a":[],"a":[]}', '{"a":[],"b":["a","a"]}', '{"a":["b"],"b":["c"],"c":["a"]}', '{"a":[null]}', '{"a":[],"é":[]}', '{"' + 'a'*33 + '":[]}']:
    try:
        core.run(raw)
    except ValueError:
        pass
    else:
        raise AssertionError(('heldout invalid accepted', raw))
print('heldout-ok')
