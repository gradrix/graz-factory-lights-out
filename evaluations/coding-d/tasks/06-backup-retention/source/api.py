import domain
def dispatch(payload):
 action=payload["action"]
 if action=='backup_ids':return domain.legacy(payload)
 raise ValueError("unknown action: "+str(action))
