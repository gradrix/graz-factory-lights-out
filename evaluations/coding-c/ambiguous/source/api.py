import domain
def dispatch(payload):
 action=payload["action"]
 if action=="identity":return domain.identity(payload)
 raise ValueError("unknown action: "+str(action))
