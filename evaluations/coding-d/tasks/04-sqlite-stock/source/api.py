import domain
def dispatch(payload):
 action=payload["action"]
 if action=='snapshot':return domain.legacy(payload)
 raise ValueError("unknown action: "+str(action))
