import domain

def dispatch(payload):
    actions={'attempts':domain.attempts}
    action=payload["action"]
    if action not in actions:raise ValueError("unknown action: "+str(action))
    return actions[action](payload)
