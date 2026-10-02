import domain
def dispatch(payload):
 action=payload["action"]
 if action=='artifact_ids':return domain.legacy(payload)
 raise ValueError("unknown action: "+str(action))
