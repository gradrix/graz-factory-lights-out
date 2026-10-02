import domain
def dispatch(payload):
 action=payload["action"]
 if action=='line_count':return domain.legacy(payload)
 raise ValueError("unknown action: "+str(action))
