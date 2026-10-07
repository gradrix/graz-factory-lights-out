import domain
def dispatch(payload):
 action=payload["action"]
 if action=='artifact_ids':return domain.legacy(payload)
 if action=='select':return domain.feature(payload)
 raise ValueError("unknown action: "+str(action))
