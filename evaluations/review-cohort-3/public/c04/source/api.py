import domain
def dispatch(payload):
 action=payload["action"]
 if action=="identity":return domain.identity(payload)
 if action in ['evaluate']:return domain.feature(payload)
 raise ValueError("unknown action: "+str(action))
