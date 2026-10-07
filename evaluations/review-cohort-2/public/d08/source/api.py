import domain
def dispatch(payload):
 action=payload["action"]
 if action=='line_count':return domain.legacy(payload)
 if action=='headings':return domain.feature(payload)
 raise ValueError("unknown action: "+str(action))
