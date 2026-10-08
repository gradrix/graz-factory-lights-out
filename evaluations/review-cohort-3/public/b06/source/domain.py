def sizes(payload):
    return sum(entry['size'] for entry in payload['entries'])

def validate(payload):
    maximum=payload['max_total'];files={};total=0
    if maximum<0:raise ValueError('limit')
    for entry in payload['entries']:
        path=entry['path'];size=entry['size']
        if not path or path.startswith('/') or '\\' in path or '\x00' in path or ':' in path or '..' in path.split('/') or size<0:raise ValueError('entry')
        path='/'.join(p for p in path.split('/') if p not in ('','.'))
        if not path or path in files:raise ValueError('path')
        files[path]=size;total+=size
    for path in files:
        parts=path.split('/')
        if any('/'.join(parts[:i]) in files for i in range(1,len(parts))):raise ValueError('ancestor')
    if total>=maximum:raise ValueError('size limit')
    return {'files':[{'path':p,'size':files[p]} for p in sorted(files)],'total':total}
