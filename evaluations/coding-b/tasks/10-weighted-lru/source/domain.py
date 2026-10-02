def weight(payload):
    return sum(entry['weight'] for entry in payload['entries'])
