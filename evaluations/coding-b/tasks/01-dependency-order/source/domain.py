def labels(payload):
    return [node['id'] for node in payload['nodes']]
