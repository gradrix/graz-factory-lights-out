import domain
def dispatch(payload):
 action=payload["action"]
 if action=='change_ids':return domain.legacy(payload)
 if action=='digest':return domain.feature(payload)
 raise ValueError("unknown action: "+str(action))
