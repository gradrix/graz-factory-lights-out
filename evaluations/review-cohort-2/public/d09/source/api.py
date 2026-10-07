import domain
def dispatch(payload):
 action=payload["action"]
 if action=='invoice_ids':return domain.legacy(payload)
 if action=='export':return domain.feature(payload)
 raise ValueError("unknown action: "+str(action))
