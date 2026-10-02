import domain
def dispatch(payload):
 if payload['action']=='total':return domain.total(payload)
 raise ValueError('unknown action')
