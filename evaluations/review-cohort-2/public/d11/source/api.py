import domain
def dispatch(payload):
 action=payload["action"]
 if action=='root_kind':return domain.legacy(payload)
 if action=='redact':return domain.feature(payload)
 raise ValueError("unknown action: "+str(action))
