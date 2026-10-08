import domain

def dispatch(payload):
    actions={'labels':domain.labels,'order':domain.order}
    action=payload["action"]
    if action not in actions:raise ValueError("unknown action: "+str(action))
    return actions[action](payload)
