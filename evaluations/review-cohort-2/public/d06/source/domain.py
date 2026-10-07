def legacy(p):return [b['id'] for b in p['backups']]

def feature(p):
 from collections import defaultdict
 groups=defaultdict(dict)
 for b in p['backups']:
  date=b['finished'][:10];old=groups[b['service']].get(date)
  if old is None or b['finished']>old['finished'] or (b['finished']==old['finished'] and b['id']>old['id']):groups[b['service']][date]=b
 keep=set()
 for dates in groups.values():
  for date in sorted(dates,reverse=True)[:p['days']]:keep.add(dates[date]['id'])
 return {k:[b['id'] for b in p['backups'] if (b['id'] in keep)==(k=='keep')] for k in ['keep','delete']}
