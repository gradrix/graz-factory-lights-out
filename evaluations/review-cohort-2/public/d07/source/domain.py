def legacy(p):return len(p['body'].encode('utf-8'))

def feature(p):
 import hashlib,hmac,re
 sig=p['signature']
 if re.fullmatch(r'sha256=[0-9a-f]{64}',sig) is None or abs(p['now']-p['timestamp'])>p['tolerance']:return False
 expected=hmac.new(p['secret'].encode(),(str(p['timestamp'])+'.'+p['body']).encode(),hashlib.sha256).hexdigest()
 return hmac.compare_digest(sig[7:],expected)
