def ids(payload):
    return [item['id'] for item in payload['items']]

from copy import deepcopy

def group(payload):
    requested=payload['requested'];responses=payload['responses'];wanted=set(requested)
    if len(wanted)!=len(requested):raise ValueError('duplicate requested')
    found={}
    for response in responses:
        key=response['id']
        if key not in wanted or key in found:raise ValueError('response id')
        found[key]=response
    out={'successes':[],'failures':[],'missing':[]}
    for key in requested:
        if key not in found:out['missing'].append(key)
        elif found[key]['ok']:out['successes'].append({'id':key,'value':deepcopy(found[key]['value'])})
        else:out['failures'].append({'id':key,'error':found[key]['error']})
    return out
