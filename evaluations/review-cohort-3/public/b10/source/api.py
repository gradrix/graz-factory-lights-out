import domain

def dispatch(payload):
    actions={'weight':domain.weight,'cache':domain.cache}
    action=payload["action"]
    if action not in actions:raise ValueError("unknown action: "+str(action))
    return actions[action](payload)
