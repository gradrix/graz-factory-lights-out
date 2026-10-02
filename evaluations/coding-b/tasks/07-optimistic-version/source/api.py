import domain

def dispatch(payload):
    actions={'read':domain.read}
    action=payload["action"]
    if action not in actions:raise ValueError("unknown action: "+str(action))
    return actions[action](payload)
