import domain

def dispatch(payload):
    actions={'length':domain.length,'index':domain.index}
    action=payload["action"]
    if action not in actions:raise ValueError("unknown action: "+str(action))
    return actions[action](payload)
