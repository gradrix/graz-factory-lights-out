def length(payload):
    return len(payload['text'])

def index(payload):
    boundaries=[0]
    for char in payload['text']:boundaries.append(boundaries[-1]+len(char.encode('utf-8')))
    inverse={byte:i for i,byte in enumerate(boundaries)}
    if any(byte not in inverse for byte in payload['byte_offsets']):raise ValueError('not a boundary')
    return {'byte_length':boundaries[-1],'char_to_byte':boundaries,'byte_to_char':[inverse[byte] for byte in payload['byte_offsets']]}
