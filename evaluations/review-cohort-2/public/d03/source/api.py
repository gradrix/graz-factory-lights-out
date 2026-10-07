import domain
def dispatch(payload):
 action=payload["action"]
 if action=='variable_names':return domain.legacy(payload)
 if action=='render':return domain.feature(payload)
 raise ValueError("unknown action: "+str(action))
