import domain
def dispatch(payload):
    if payload["action"]!="order":raise ValueError("unknown action")
    return domain.order(payload)
