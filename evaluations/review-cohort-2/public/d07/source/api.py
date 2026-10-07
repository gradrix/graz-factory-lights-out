import domain
def dispatch(payload):
 action=payload["action"]
 if action=='body_bytes':return domain.legacy(payload)
 if action=='verify':return domain.feature(payload)
 raise ValueError("unknown action: "+str(action))
