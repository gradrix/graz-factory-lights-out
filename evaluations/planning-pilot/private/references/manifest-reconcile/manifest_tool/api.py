from .domain import compare
from .report import totals

def run(payload):
    if payload=={'action':'ping'}:return {'ok':True}
    if not isinstance(payload,dict) or set(payload)!={'action','before','after'} or payload['action']!='compare':raise ValueError('payload')
    result=compare(payload['before'],payload['after']);result['summary']=totals(payload['before'],payload['after']);return result
