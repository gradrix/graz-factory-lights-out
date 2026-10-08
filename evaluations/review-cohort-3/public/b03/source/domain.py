def attempts(payload):
    return len(payload['outcomes'])

def schedule(payload):
    now=payload['now']; attempt=payload['attempt'];base=payload['base'];cap=payload['cap'];maximum=payload['max_attempts'];outcome=payload['outcome'];after=payload.get('retry_after')
    if any(type(x) is not int or x<1 for x in [attempt,base,cap,maximum]): raise ValueError('bounds')
    if after is not None and (type(after) is not int or after<0): raise ValueError('retry_after')
    if outcome not in {'success','permanent','transient'}: raise ValueError('outcome')
    if outcome!='transient' or attempt>=maximum:return {'retry':False,'at':None,'delay':None}
    # Avoid constructing an enormous integer once the cap is already reached.
    delay=base
    for unused in range(attempt-1):
        if delay>=cap:break
        delay*=2
    delay=max(min(cap,delay),after or 0)
    return {'retry':True,'at':now+delay,'delay':delay}
