import domain
def dispatch(payload):
 action=payload["action"]
 if action=='emails':return domain.legacy(payload)
 raise ValueError("unknown action: "+str(action))
