def total(payload):
 values=payload['values']
 if not isinstance(values,list) or any(type(v) is not int for v in values):raise ValueError('integer values required')
 return sum(values)
