import domain

def dispatch(payload):
    actions={'count':domain.count,'admit':domain.admit}
    action=payload["action"]
    if action not in actions:raise ValueError("unknown action: "+str(action))
    return actions[action](payload)
