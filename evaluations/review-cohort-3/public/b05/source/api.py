import domain

def dispatch(payload):
    actions={'field_names':domain.field_names,'encode':domain.encode,'decode':domain.decode}
    action=payload["action"]
    if action not in actions:raise ValueError("unknown action: "+str(action))
    return actions[action](payload)
