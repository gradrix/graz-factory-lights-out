from collections import deque

def labels(payload):
    return [node['id'] for node in payload['nodes']]

def order(payload):
    nodes=payload['nodes']; positions={n['id']:i for i,n in enumerate(nodes)}
    if len(positions)!=len(nodes): raise ValueError('duplicate id')
    dependencies={n['id']:set(n['deps']) for n in nodes}
    if any(not deps <= positions.keys() for deps in dependencies.values()): raise ValueError('unknown dependency')
    dependents={n['id']:[] for n in nodes}
    for n in nodes:
        for dep in dependencies[n['id']]: dependents[dep].append(n['id'])
    waiting={key:len(deps) for key,deps in dependencies.items()}
    ready=deque(n['id'] for n in nodes if not waiting[n['id']])
    result=[]
    while ready:
        chosen=ready.popleft();result.append(chosen)
        for other in dependents[chosen]:
            waiting[other]-=1
            if not waiting[other]: ready.append(other)
    if len(result)!=len(nodes): raise ValueError('cycle')
    return result
