import domain

def dispatch(payload):
    actions={'labels':domain.labels}
    action=payload["action"]
    if action not in actions:raise ValueError("unknown action: "+str(action))
    return actions[action](payload)
