def count(payload):
    return len(payload['events'])

def admit(payload):
    history=payload['history'];now=payload['now'];window=payload['window'];limit=payload['limit']
    if type(window) is not int or window<=0 or type(limit) is not int or limit<0: raise ValueError('limits')
    if history!=sorted(history) or any(t>now for t in history): raise ValueError('history')
    active=[t for t in history if t>now-window]
    if len(active)<limit: return {'allowed':True,'history':active+[now],'retry_at':None}
    retry=None if limit==0 else active[len(active)-limit]+window
    return {'allowed':False,'history':active,'retry_at':retry}
