def sources(payload):
    return sorted({event['source'] for event in payload['events']})
