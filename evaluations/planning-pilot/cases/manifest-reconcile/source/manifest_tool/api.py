def run(payload):
    if payload=={'action':'ping'}:return {'ok':True}
    raise ValueError('unknown action')
