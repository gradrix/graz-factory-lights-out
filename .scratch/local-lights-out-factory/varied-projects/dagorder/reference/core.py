import json, re

def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate key')
        result[key] = value
    return result

def run(text):
    if not isinstance(text, str):
        raise ValueError('text required')
    graph = json.loads(text, object_pairs_hook=_object)
    if not isinstance(graph, dict):
        raise ValueError('object required')
    for node, deps in graph.items():
        if not re.fullmatch(r'[a-z][a-z0-9_]{0,31}', node) or not isinstance(deps, list):
            raise ValueError('node')
        if any(not isinstance(d, str) or d not in graph for d in deps):
            raise ValueError('prerequisite')
        if len(set(deps)) != len(deps):
            raise ValueError('duplicate prerequisite')
    result = []
    remaining = set(graph)
    while remaining:
        ready = sorted(n for n in remaining if all(d in result for d in graph[n]))
        if not ready:
            raise ValueError('cycle')
        result.append(ready[0])
        remaining.remove(ready[0])
    return result
