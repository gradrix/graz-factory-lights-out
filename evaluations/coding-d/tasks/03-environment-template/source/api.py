import domain
def dispatch(payload):
 action=payload["action"]
 if action=='variable_names':return domain.legacy(payload)
 raise ValueError("unknown action: "+str(action))
