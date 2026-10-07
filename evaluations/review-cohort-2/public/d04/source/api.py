import domain
def dispatch(payload):
 action=payload["action"]
 if action=='snapshot':return domain.legacy(payload)
 if action=='adjust':return domain.feature(payload)
 raise ValueError("unknown action: "+str(action))
