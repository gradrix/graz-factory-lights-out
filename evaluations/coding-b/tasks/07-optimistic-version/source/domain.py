from copy import deepcopy

def read(payload):
    return deepcopy(payload['records'].get(payload['id']))
