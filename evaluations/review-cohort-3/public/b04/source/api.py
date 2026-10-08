import domain

def dispatch(payload):
    actions={'keys':domain.keys,'resolve':domain.resolve}
    action=payload["action"]
    if action not in actions:raise ValueError("unknown action: "+str(action))
    return actions[action](payload)
