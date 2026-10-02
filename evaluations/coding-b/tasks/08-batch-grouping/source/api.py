import domain

def dispatch(payload):
    actions={'ids':domain.ids}
    action=payload["action"]
    if action not in actions:raise ValueError("unknown action: "+str(action))
    return actions[action](payload)
