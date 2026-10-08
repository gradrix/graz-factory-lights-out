def identity(payload):
 return payload['value']

def feature(p):
 import datetime,calendar
 start=datetime.date.fromisoformat(p['start']);y,m=start.year,start.month;out=[]
 while len(out)<p['count']:
  d=datetime.date(y,m,min(p['day'],calendar.monthrange(y,m)[1]))
  if d>=start:out.append(d.isoformat())
  m+=1
  if m==13:y+=1;m=1
 return out
