def keys(payload):
    return sorted(payload['config'])

from copy import deepcopy

def resolve(payload):
    def overlay(target,new):
        for key,value in new.items():
            if value is None:target.pop(key,None)
            elif isinstance(value,dict):
                if not isinstance(target.get(key),dict):target[key]={}
                overlay(target[key],value)
            else:target[key]=deepcopy(value)
        return target
    out=dict(payload['defaults'])
    for layer in payload['layers']:out=overlay(out,layer)
    if any(key not in out for key in payload['required']):raise ValueError('missing required')
    return out
