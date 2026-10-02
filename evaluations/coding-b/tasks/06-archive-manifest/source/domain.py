def sizes(payload):
    return sum(entry['size'] for entry in payload['entries'])
