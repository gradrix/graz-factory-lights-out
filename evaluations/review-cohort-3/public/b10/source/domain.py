def weight(payload):
    return sum(entry['weight'] for entry in payload['entries'])

from copy import deepcopy
from collections import OrderedDict

def cache(payload):
    capacity=payload['capacity']
    if capacity<0:raise ValueError('capacity')
    items=OrderedDict();results=[]
    for op in payload['operations']:
        key=op['key']
        if op['op']=='get':
            if key in items:
                items.move_to_end(key);results.append({'hit':True,'value':deepcopy(items[key]['value'])})
            else:results.append({'hit':False,'value':None})
        else:
            weight=op['weight']
            if weight<=0:raise ValueError('weight')
            if weight>capacity:results.append({'stored':False,'evicted':[]});continue
            items.pop(key,None);items[key]={'key':key,'value':deepcopy(op['value']),'weight':weight};evicted=[]
            while sum(v['weight'] for v in items.values())>capacity:evicted.append(items.popitem(last=False)[0])
            results.append({'stored':True,'evicted':evicted})
    return {'results':results,'entries':list(items.values())}
