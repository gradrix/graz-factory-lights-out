def legacy(p):return [x['email'] for x in p['existing']]

def feature(p):
 import csv,io
 rows=list(csv.reader(io.StringIO(p['csv'],newline='')))
 if not rows or rows[0]!=['email','name']:raise ValueError('header')
 seen={x['email'] for x in p['existing']};out=[];skipped=0
 for row in rows[1:]:
  if len(row)!=2:raise ValueError('columns')
  e,n=(x.strip() for x in row);e=e.lower()
  if e.count('@')!=1 or not all(e.split('@')) or any(c.isspace() for c in e) or not n:raise ValueError('contact')
  if e in seen:skipped+=1
  else:seen.add(e);out.append({'email':e,'name':n})
 return {'added':out,'skipped':skipped}
