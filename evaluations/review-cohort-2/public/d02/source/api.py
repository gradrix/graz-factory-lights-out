import domain
def dispatch(payload):
 action=payload["action"]
 if action=='routes':return domain.legacy(payload)
 if action=='report':return domain.feature(payload)
 raise ValueError("unknown action: "+str(action))
