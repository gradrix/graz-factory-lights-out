def legacy(p):
 v=p['document']
 return 'object' if isinstance(v,dict) else 'array' if isinstance(v,list) else 'scalar'
