import json,pathlib,textwrap,subprocess
R=pathlib.Path(__file__).resolve().parents[1]
ITEMS=[]
def add(name,title,spec,code,cases,errors,old_action,old_code,old_input,old_output):
 ITEMS.append(dict(name=name,title=title,spec=spec,code=textwrap.dedent(code),cases=cases,errors=errors,old_action=old_action,old_code=textwrap.dedent(old_code),old_input=old_input,old_output=old_output))
add('contact-import','Contact import preview',
'''Add action import_contacts with csv: a string of valid CSV syntax, up to 200 rows and 10000 code points, and existing: a list of contact objects {email,name}. Existing email strings are already unique normalized lowercase ASCII. Parse comma-separated CSV with the standard double-quote quoting convention. The header must be exactly email,name in that order; each subsequent record must have exactly two columns. A contact email after stripping surrounding whitespace and lowercasing must have exactly one @, nonempty parts on both sides, and no whitespace anywhere. A stripped name must be nonempty. Invalid header, column count, email or name raises ValueError. Deduplicate new email addresses after normalization: retain their first CSV occurrence, then discard those already present in existing. Return {added:[{email,name},...], skipped:integer}; skipped counts every valid CSV data record not added (including repeat occurrences). Validate every record, even duplicates that would be skipped. Do not change existing. A header-only CSV is valid; an empty string is invalid. Embedded quoted newlines in names are allowed.''',
r'''
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
''',[
({'csv':'email,name\n A@X , Ada \na@x,Ignored\nb@x,"Bee, Two"\n','existing':[]},{'added':[{'email':'a@x','name':'Ada'},{'email':'b@x','name':'Bee, Two'}],'skipped':1}),
({'csv':'email,name\na@x,A\nc@x,C\na@x,A2\n','existing':[{'email':'a@x','name':'Old'}]},{'added':[{'email':'c@x','name':'C'}],'skipped':2}),
({'csv':'email,name\n','existing':[]},{'added':[],'skipped':0}),
({'csv':'email,name\nz@x,"Line one\nLine two"\n','existing':[]},{'added':[{'email':'z@x','name':'Line one\nLine two'}],'skipped':0})],
[{'csv':s,'existing':[]} for s in ['', 'name,email\nA,a@x','email,name\na@x,A,extra','email,name\na@@x,A','email,name\na@x, ','email,name\na@x,A\na@x, ','email,name\na @x,A']],
'emails',"def legacy(p):return [x['email'] for x in p['existing']]\n",{'existing':[{'email':'z@x','name':'Z'},{'email':'a@x','name':'A'}]},['z@x','a@x'])
add('access-report','HTTP access report',
'''Add action report with entries: list of {route:string,status:integer 100..599,ms:nonnegative integer}, and min_requests: integer 1..200. At most 200 entries, route strings 1..100 code points. Group by exact route. Return a list sorted by route in Python string order; omit groups with fewer than min_requests entries. Each row is {route,requests,errors,p95_ms}. Errors count status >=500. The p95 is nearest rank: sort milliseconds ascending and choose the ceil(0.95*n)-th value counting from one. Never round an averaged percentile. Empty entries yields [].''',
r'''
def feature(p):
 from collections import defaultdict
 groups=defaultdict(list)
 for e in p['entries']:groups[e['route']].append(e)
 out=[]
 for route,es in sorted(groups.items()):
  n=len(es)
  if n>=p['min_requests']:out.append({'route':route,'requests':n,'errors':sum(e['status']>=500 for e in es),'p95_ms':sorted(e['ms'] for e in es)[(95*n+99)//100-1]})
 return out
''',[
({'entries':[{'route':'/b','status':503,'ms':90},{'route':'/a','status':404,'ms':0},{'route':'/b','status':200,'ms':10}],'min_requests':1},[{'route':'/a','requests':1,'errors':0,'p95_ms':0},{'route':'/b','requests':2,'errors':1,'p95_ms':90}]),
({'entries':[{'route':'/x','status':200,'ms':i} for i in range(1,21)],'min_requests':20},[{'route':'/x','requests':20,'errors':0,'p95_ms':19}]),
({'entries':[],'min_requests':1},[]),
({'entries':[{'route':'/x','status':500,'ms':1}],'min_requests':2},[])],[],
'routes',"def legacy(p):return [e['route'] for e in p['entries']]\n",{'entries':[{'route':'/b','status':200,'ms':1},{'route':'/a','status':200,'ms':2}]},['/b','/a'])
add('environment-template','Environment template renderer',
'''Add action render with template: string <=4000 code points, variables: object mapping names to string values (<=100 names, values <=1000 code points). Names match ASCII [A-Za-z_][A-Za-z0-9_]*. Scan template left to right: $$ emits one literal dollar; ${NAME} substitutes its variable; any other dollar, malformed name, missing closing brace or undefined variable raises ValueError. A single-pass substitution is required: dollar text inside a variable value is literal and is never expanded. Text outside substitutions is preserved exactly, including newlines. Return rendered string. Empty template is valid. Escaped dollars consume two characters, so $${X} yields literal ${X}.''',
r'''
def feature(p):
 import re
 s=p['template'];out=[];i=0
 while i<len(s):
  if s[i]!='$':out.append(s[i]);i+=1;continue
  if s[i:i+2]=='$$':out.append('$');i+=2;continue
  if s[i:i+2]!='${':raise ValueError('dollar')
  end=s.find('}',i+2)
  if end<0:raise ValueError('brace')
  name=s[i+2:end]
  if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',name) is None or name not in p['variables']:raise ValueError('variable')
  out.append(p['variables'][name]);i=end+1
 return ''.join(out)
''',[
({'template':'host=${HOST}\nport=${PORT}','variables':{'HOST':'example','PORT':'443'}},'host=example\nport=443'),
({'template':'$${X}:$$:${X}','variables':{'X':'${Y}'}},'${X}:$:${Y}'),
({'template':'','variables':{}},''),
({'template':'${_A1}${_A1}','variables':{'_A1':'é'}},'éé')],
[{'template':s,'variables':{}} for s in ['$', '$x', '${}', '${X}', '${A', '${a-b}']],
'variable_names',"def legacy(p):return sorted(p['variables'])\n",{'variables':{'Z':'z','A':'a'}},['A','Z'])
add('sqlite-stock','Atomic warehouse adjustments',
'''The warehouse SQLite database has exactly table stock(sku TEXT PRIMARY KEY, quantity INTEGER NOT NULL) with nonnegative quantities. Add action adjust with db: absolute path to an existing writable database and changes: list of {sku:nonempty string,delta:integer -1000..1000}, up to 100 changes. Apply changes in input order in ONE atomic transaction. A missing SKU or an intermediate quantity below zero raises ValueError and rolls back every change from that call. Repeated SKUs are allowed; apply each delta to the latest quantity. On success return all rows as [{sku,quantity},...] sorted by sku using Python string order, and persist them. Empty changes returns current rows. No new rows or schema changes. Preserve the existing action snapshot and its output. Only the named database may be changed; close resources before returning. The fixture is a local database with no concurrent clients. The baseline snapshot takes {action:"snapshot",db:path}.''',
r'''
def feature(p):
 import sqlite3
 con=sqlite3.connect(p['db'])
 try:
  with con:
   for item in p['changes']:
    row=con.execute('SELECT quantity FROM stock WHERE sku=?',(item['sku'],)).fetchone()
    if row is None or row[0]+item['delta']<0:raise ValueError('invalid adjustment')
    con.execute('UPDATE stock SET quantity=? WHERE sku=?',(row[0]+item['delta'],item['sku']))
  return legacy(p)
 finally:con.close()
''',[
({'changes':[{'sku':'a','delta':-2},{'sku':'b','delta':3}]},[{'sku':'a','quantity':3},{'sku':'b','quantity':5}]),
({'changes':[{'sku':'a','delta':-5},{'sku':'a','delta':2}]},[{'sku':'a','quantity':2},{'sku':'b','quantity':2}]),
({'changes':[]},[{'sku':'a','quantity':5},{'sku':'b','quantity':2}])],
[{'changes':[{'sku':'a','delta':-1},{'sku':'missing','delta':1}]},{'changes':[{'sku':'b','delta':-3},{'sku':'b','delta':3}]},{'changes':[{'sku':'a','delta':-5},{'sku':'a','delta':-1}]}],
'snapshot',"""def legacy(p):
 import sqlite3
 con=sqlite3.connect(p['db'])
 try:return [{'sku':s,'quantity':q} for s,q in sorted(con.execute('SELECT sku,quantity FROM stock').fetchall())]
 finally:con.close()
""",{},[{'sku':'a','quantity':5},{'sku':'b','quantity':2}])
add('release-digest','Release digest builder',
'''Add action digest with changes: list of {id:nonempty string,category:one of added/fixed/removed,title:string,internal:boolean}, up to 200 rows. First deduplicate all rows by id, retaining the LAST occurrence and its position. Then omit retained internal rows. Return a Markdown string containing nonempty category sections in fixed order added, fixed, removed, headed exactly ## Added / ## Fixed / ## Removed. Within a section retain surviving last-occurrence order. A bullet is "- " plus title with each run of whitespace replaced by one ASCII space and leading/trailing whitespace stripped. Separate sections by one blank line, finish any nonempty output with one newline; no changes returns empty string. Titles may contain Markdown punctuation, which is preserved literally; no escaping is requested.''',
r'''
def feature(p):
 last={c['id']:i for i,c in enumerate(p['changes'])};sections=[]
 for cat in ['added','fixed','removed']:
  rows=[c for i,c in enumerate(p['changes']) if last[c['id']]==i and not c['internal'] and c['category']==cat]
  if rows:sections.append('## '+cat.title()+'\n'+'\n'.join('- '+' '.join(c['title'].split()) for c in rows))
 return '\n\n'.join(sections)+'\n' if sections else ''
''',[
({'changes':[{'id':'1','category':'fixed','title':' A\n fix ','internal':False},{'id':'2','category':'added','title':'New **API**','internal':False}]},'## Added\n- New **API**\n\n## Fixed\n- A fix\n'),
({'changes':[{'id':'x','category':'added','title':'Old','internal':False},{'id':'y','category':'added','title':'Y','internal':False},{'id':'x','category':'fixed','title':'Secret','internal':True}]},'## Added\n- Y\n'),
({'changes':[]},''),
({'changes':[{'id':'a','category':'removed','title':'  ','internal':False}]},'## Removed\n- \n')],[],
'change_ids',"def legacy(p):return [c['id'] for c in p['changes']]\n",{'changes':[{'id':'x'},{'id':'x'}]},['x','x'])
add('backup-retention','Daily backup retention plan',
'''Add action plan with backups: list of {id:unique nonempty string,service:nonempty string,finished:UTC timestamp exactly YYYY-MM-DDTHH:MM:SSZ}, and days: integer 0..30. Inputs have valid calendar timestamps in 2000..2090, at most 200 backups. For EACH service retain only the latest backup on each of its newest days distinct UTC calendar dates. If backups on one date have identical finished timestamps, retain the smallest id in Python string order. Return {keep:[ids],delete:[ids]}, both lists in original backup input order. days=0 deletes all. Different services have separate retention counts. This is a preview only and must not access files.''',
r'''
def feature(p):
 from collections import defaultdict
 groups=defaultdict(dict)
 for b in p['backups']:
  date=b['finished'][:10];old=groups[b['service']].get(date)
  if old is None or b['finished']>old['finished'] or (b['finished']==old['finished'] and b['id']<old['id']):groups[b['service']][date]=b
 keep=set()
 for dates in groups.values():
  for date in sorted(dates,reverse=True)[:p['days']]:keep.add(dates[date]['id'])
 return {k:[b['id'] for b in p['backups'] if (b['id'] in keep)==(k=='keep')] for k in ['keep','delete']}
''',[
({'backups':[{'id':'old','service':'db','finished':'2026-01-01T10:00:00Z'},{'id':'early','service':'db','finished':'2026-01-02T10:00:00Z'},{'id':'late','service':'db','finished':'2026-01-02T11:00:00Z'},{'id':'web','service':'web','finished':'2025-12-01T00:00:00Z'}],'days':1},{'keep':['late','web'],'delete':['old','early']}),
({'backups':[{'id':'z','service':'x','finished':'2026-01-01T00:00:00Z'},{'id':'a','service':'x','finished':'2026-01-01T00:00:00Z'}],'days':3},{'keep':['a'],'delete':['z']}),
({'backups':[],'days':0},{'keep':[],'delete':[]}),
({'backups':[{'id':'x','service':'x','finished':'2026-01-01T00:00:00Z'}],'days':0},{'keep':[],'delete':['x']})],[],
'backup_ids',"def legacy(p):return [b['id'] for b in p['backups']]\n",{'backups':[{'id':'b'},{'id':'a'}]},['b','a'])
add('webhook-auth','Webhook authentication utility',
'''Add action verify with secret:string, body:string, timestamp:nonnegative integer <=2**40, now:nonnegative integer <=2**40, tolerance:integer 0..3600, signature:string. Strings secret/body are <=4000 Unicode code points. Compute HMAC-SHA256 using UTF-8 secret over UTF-8 bytes of decimal timestamp + "." + body. Return a JSON boolean true only when signature is exactly "sha256=" followed by 64 lowercase hex characters equal to that digest AND abs(now-timestamp)<=tolerance. Otherwise return false. Signature is untrusted and may contain any Unicode characters, including empty input. No exceptions for malformed signature. Use a timing-safe digest comparison for well-formed signatures. Never log or return secrets or body.''',
r'''
def feature(p):
 import hashlib,hmac,re
 sig=p['signature']
 if re.fullmatch(r'sha256=[0-9a-f]{64}',sig) is None or abs(p['now']-p['timestamp'])>p['tolerance']:return False
 expected=hmac.new(p['secret'].encode(),(str(p['timestamp'])+'.'+p['body']).encode(),hashlib.sha256).hexdigest()
 return hmac.compare_digest(sig[7:],expected)
''',[],[],
'body_bytes',"def legacy(p):return len(p['body'].encode('utf-8'))\n",{'body':'é猫'},5)
add('markdown-index','Markdown heading catalog',
'''Add action headings with markdown:string <=10000 code points. Process splitlines() lines in order, line numbers start at one. A fence is any line whose stripped text starts with three backticks; each such line toggles fenced mode and is excluded, regardless of remaining text. Exclude all lines in fenced mode. Outside fences, recognize only lines beginning at column zero with 1..6 # characters followed by one ASCII space. The heading text is the remainder after that one space, stripped at both ends; trailing # are ordinary text. Return [{level:integer,text:string,line:integer,anchor:string}]. Anchor base: lowercase text, keep only ASCII a-z/0-9 and ASCII spaces/hyphens, replace each run of spaces/hyphens with one hyphen, trim hyphens. Empty base becomes "section". Ensure anchors are unique globally in order: use base if unused; otherwise try base-2, base-3, etc until unused, including collisions with earlier literal bases. Do not modify markdown.''',
r'''
def feature(p):
 import re
 fenced=False;used=set();out=[]
 for i,line in enumerate(p['markdown'].splitlines(),1):
  if line.strip().startswith('```'):fenced=not fenced;continue
  if fenced:continue
  m=re.match(r'^(#{1,6}) (.*)$',line)
  if not m:continue
  text=m[2].strip();base=re.sub(r'[^a-z0-9 -]','',text.lower());base=re.sub(r'[ -]+','-',base).strip('-') or 'section'
  anchor=base;n=2
  while anchor in used:anchor=base+'-'+str(n);n+=1
  used.add(anchor);out.append({'level':len(m[1]),'text':text,'line':i,'anchor':anchor})
 return out
''',[
({'markdown':'# Hello World\ntext\n## Hello World\n'},[{'level':1,'text':'Hello World','line':1,'anchor':'hello-world'},{'level':2,'text':'Hello World','line':3,'anchor':'hello-world-2'}]),
({'markdown':'```python\n# hidden\n```\n # indented\n####### too deep\n#No space\n# !!!'},[{'level':1,'text':'!!!','line':7,'anchor':'section'}]),
({'markdown':'# A\n# A-2\n# A\n# Café --- X'},[{'level':1,'text':'A','line':1,'anchor':'a'},{'level':1,'text':'A-2','line':2,'anchor':'a-2'},{'level':1,'text':'A','line':3,'anchor':'a-3'},{'level':1,'text':'Café --- X','line':4,'anchor':'caf-x'}]),
({'markdown':''},[])],[],
'line_count',"def legacy(p):return len(p['markdown'].splitlines())\n",{'markdown':'a\nb\n'},2)
add('invoice-csv','Invoice CSV exporter',
'''Add action export with invoices:list of {id:nonempty string,customer:string,items:list of {quantity:integer 0..1000,unit_cents:integer 0..1000000}}, up to 100 invoices and 100 items each. Return a CSV string with header id,customer,total and one row per invoice in input order. total is exact sum(quantity*unit_cents), expressed in decimal currency units with exactly two fractional digits and no thousands separator. Empty items total is 0.00. Use standard CSV quoting: comma separator, quote fields containing comma, double quote, carriage return or newline; embedded quotes doubled; every record terminates with CRLF, including header and final row. Do not normalize text. ids/customer <=200 code points. Empty invoices still returns header.''',
r'''
def feature(p):
 import csv,io
 stream=io.StringIO(newline='');w=csv.writer(stream,lineterminator='\r\n');w.writerow(['id','customer','total'])
 for inv in p['invoices']:
  cents=sum(x['quantity']*x['unit_cents'] for x in inv['items']);w.writerow([inv['id'],inv['customer'],str(cents//100)+'.'+str(cents%100).zfill(2)])
 return stream.getvalue()
''',[
({'invoices':[{'id':'a','customer':'Ada','items':[{'quantity':3,'unit_cents':105},{'quantity':0,'unit_cents':1}]}]},'id,customer,total\r\na,Ada,3.15\r\n'),
({'invoices':[{'id':'a,1','customer':'"X"\nY','items':[]}]},'id,customer,total\r\n"a,1","""X""\nY",0.00\r\n'),
({'invoices':[]},'id,customer,total\r\n'),
({'invoices':[{'id':'max','customer':'猫','items':[{'quantity':1000,'unit_cents':1000000}]}]},'id,customer,total\r\nmax,猫,10000000.00\r\n')],[],
'invoice_ids',"def legacy(p):return [x['id'] for x in p['invoices']]\n",{'invoices':[{'id':'b'},{'id':'a'}]},['b','a'])
add('service-readiness','Service readiness summary',
'''Add action readiness with required:list of unique service names, checks:list of {service:string,state:one of up/down/unknown,critical:boolean}, and quorum:integer 0..100. Up to 100 required names and 200 checks. For each service mentioned in required or checks, use ONLY its LAST check; missing required services count unknown and noncritical. Return {ready:boolean,up:integer,blockers:[service names]}. up counts distinct services whose last state is up, including services not required. blockers includes every required service whose last state is not up or missing, plus every service whose last check is critical and not up. Deduplicate blockers and sort by Python string order. ready is true exactly when up>=quorum and blockers is empty. Earlier critical flags have no effect once replaced. Empty inputs with quorum 0 is ready.''',
r'''
def feature(p):
 last={c['service']:c for c in p['checks']};up=sum(c['state']=='up' for c in last.values());block=set()
 for s in p['required']:
  if s not in last or last[s]['state']!='up':block.add(s)
 for s,c in last.items():
  if c['critical'] and c['state']!='up':block.add(s)
 return {'ready':up>=p['quorum'] and not block,'up':up,'blockers':sorted(block)}
''',[
({'required':['db'],'checks':[{'service':'db','state':'up','critical':True},{'service':'web','state':'up','critical':False}],'quorum':2},{'ready':True,'up':2,'blockers':[]}),
({'required':['db','cache'],'checks':[{'service':'db','state':'down','critical':False},{'service':'mail','state':'unknown','critical':True}],'quorum':0},{'ready':False,'up':0,'blockers':['cache','db','mail']}),
({'required':[],'checks':[{'service':'x','state':'down','critical':True},{'service':'x','state':'unknown','critical':False}],'quorum':0},{'ready':True,'up':0,'blockers':[]}),
({'required':[],'checks':[],'quorum':1},{'ready':False,'up':0,'blockers':[]}),
({'required':[],'checks':[],'quorum':0},{'ready':True,'up':0,'blockers':[]})],[],
'check_names',"def legacy(p):return [c['service'] for c in p['checks']]\n",{'checks':[{'service':'x'},{'service':'x'}]},['x','x'])
add('support-redaction','Support bundle redaction',
'''Add action redact with document:any JSON value with nesting depth <=10 and <=500 values, keys:list of strings (<=50), replacement:any scalar JSON value (null, boolean, integer, string; integers magnitude <=10**12). Return a deep copy of document where every object member whose key case-insensitively matches a listed key is replaced with replacement, at any depth. Case-insensitive means Python str.casefold(), with no whitespace stripping. Arrays are traversed, scalars stay unchanged; when replacing an object member, replace its entire value without traversing it further. Preserve object keys, array order, and exact types of untouched values. No in-place mutation or aliasing of returned mutable containers to input containers. document contains null, booleans, integers, strings, lists, and string-keyed objects; no floats.''',
r'''
def feature(p):
 names={k.casefold() for k in p['keys']}
 def walk(v):
  if isinstance(v,dict):return {k:p['replacement'] if k.casefold() in names else walk(x) for k,x in v.items()}
  if isinstance(v,list):return [walk(x) for x in v]
  return v
 return walk(p['document'])
''',[
({'document':{'Token':'s','nested':[{'token':{'a':1},'keep':False},True]},'keys':['TOKEN'],'replacement':'***'},{'Token':'***','nested':[{'token':'***','keep':False},True]}),
({'document':{'STRASSE':'secret',' token ':'keep'},'keys':['straße','token'],'replacement':None},{'STRASSE':None,' token ':'keep'}),
({'document':[1,True,None],'keys':[],'replacement':0},[1,True,None]),
({'document':False,'keys':['x'],'replacement':'x'},False)],[],
'root_kind',"""def legacy(p):
 v=p['document']
 return 'object' if isinstance(v,dict) else 'array' if isinstance(v,list) else 'scalar'
""",{'document':{'x':False}},'object')
add('artifact-selector','Release artifact selector',
'''Add action select with artifacts:list of {id:unique nonempty string,platform:string,version:string,yanked:boolean}, platform:string, major:integer 0..1000. At most 200 artifacts. Every version is exactly three unsigned ASCII decimal components with no leading zero except 0, each 0..1000, separated by periods; versions have no prerelease/build suffix. Return null when no eligible artifact exists. Eligible means matching exact platform, major component equal to requested major, and yanked=false. Otherwise return {id,version} for numerically greatest (major,minor,patch), breaking equal-version ties by smallest id in Python string order. Input order never breaks ties. Preserve version spelling and input objects.''',
r'''
def feature(p):
 eligible=[a for a in p['artifacts'] if a['platform']==p['platform'] and not a['yanked'] and int(a['version'].split('.')[0])==p['major']]
 if not eligible:return None
 a=min(eligible,key=lambda a:(tuple(-int(x) for x in a['version'].split('.')),a['id']))
 return {'id':a['id'],'version':a['version']}
''',[
({'artifacts':[{'id':'a','platform':'linux','version':'1.9.9','yanked':False},{'id':'b','platform':'linux','version':'1.10.0','yanked':False},{'id':'c','platform':'linux','version':'2.0.0','yanked':False}],'platform':'linux','major':1},{'id':'b','version':'1.10.0'}),
({'artifacts':[{'id':'z','platform':'x','version':'0.1.0','yanked':False},{'id':'a','platform':'x','version':'0.1.0','yanked':False},{'id':'y','platform':'x','version':'0.2.0','yanked':True}],'platform':'x','major':0},{'id':'a','version':'0.1.0'}),
({'artifacts':[],'platform':'x','major':1},None),
({'artifacts':[{'id':'a','platform':'mac','version':'1.0.0','yanked':False}],'platform':'linux','major':1},None)],[],
'artifact_ids',"def legacy(p):return [a['id'] for a in p['artifacts']]\n",{'artifacts':[{'id':'b'},{'id':'a'}]},['b','a'])
# Independently fixed HMAC examples are prepared without calling the implementation.
import hmac,hashlib
web=ITEMS[6]
for secret,body,timestamp,now,tolerance,valid in [('key','{}',100,105,5,True),('é','猫\n',0,0,0,True),('key','{}',100,94,5,False),('','',2**40,2**40,0,True)]:
 signature='sha256='+hmac.new(secret.encode(),(str(timestamp)+'.'+body).encode(),hashlib.sha256).hexdigest()
 web['cases'].append((dict(secret=secret,body=body,timestamp=timestamp,now=now,tolerance=tolerance,signature=signature),valid))
for signature in ['','sha256='+'A'*64,'sha256='+'0'*64,'sha256=é','sha256='+'a'*63]:
 web['cases'].append((dict(secret='key',body='{}',timestamp=100,now=100,tolerance=0,signature=signature),False))
ACTIONS=['import_contacts','report','render','adjust','digest','plan','verify','headings','export','readiness','redact','select']
CLI='''import json,sys
from api import dispatch
def main():
 try:result=dispatch(json.load(sys.stdin))
 except ValueError as error:
  print(str(error),file=sys.stderr);return 2
 print(json.dumps(result,ensure_ascii=False));return 0
if __name__=='__main__':raise SystemExit(main())
'''
def api(old,new,ref):
 return 'import domain\ndef dispatch(payload):\n action=payload["action"]\n if action=='+repr(old)+':return domain.legacy(payload)\n'+(' if action=='+repr(new)+':return domain.feature(payload)\n' if ref else '')+' raise ValueError("unknown action: "+str(action))\n'
COMMON=''' Implement domain.py, api.dispatch(payload), and existing python cli.py JSON stdin/stdout routing. Preserve documented existing action, successful CLI JSON behavior, unknown-action ValueError, and CLI exit 2 with nonempty stderr/no traceback for ValueError. Preserve all specified JSON types exactly (booleans are not integers). Never mutate input objects, even on failure. Python 3.12+, standard library, UTF-8; input shapes and types follow the contract except explicitly described errors. Do not invent validation or business policy. Add at least three meaningful public-behavior unittest test methods discoverable with python -m unittest discover; cover a normal case, a boundary, and a specified rejection (or another boundary when no rejection is specified). Tests must pass. Update README.md with new action usage, a concrete python cli.py JSON invocation, and boundary/error semantics, at least 40 words in complete README. You may add modules/helpers; preserve public interfaces.'''
HELPER='''def json_equal(a,b):
 if type(a) is not type(b):return False
 if isinstance(b,dict):return a.keys()==b.keys() and all(json_equal(a[k],b[k]) for k in b)
 if isinstance(b,list):return len(a)==len(b) and all(json_equal(x,y) for x,y in zip(a,b))
 return a==b
'''
ORACLE=r'''import copy,json,pathlib,subprocess,sys,tempfile,sqlite3,unittest
sys.path.insert(0,str(pathlib.Path.cwd()))
from api import dispatch
HELPER
DATA
arena=tempfile.TemporaryDirectory()
counter=0
def prepare(p):
 global counter
 p=copy.deepcopy(p)
 if database:
  counter+=1;p['db']=str(pathlib.Path(arena.name)/('stock'+str(counter)+'.db'))
  with sqlite3.connect(p['db']) as con:
   con.execute('CREATE TABLE stock(sku TEXT PRIMARY KEY,quantity INTEGER NOT NULL)')
   con.executemany('INSERT INTO stock VALUES (?,?)',[('a',5),('b',2)])
 return p
def rows(p):
 with sqlite3.connect(p['db']) as con:return [{'sku':s,'quantity':q} for s,q in sorted(con.execute('SELECT sku,quantity FROM stock').fetchall())]
def check(p,want,error=False):
 original=prepare(p);given=copy.deepcopy(original)
 if error:
  try:dispatch(given)
  except ValueError:pass
  else:raise AssertionError('expected ValueError')
 else:
  actual=dispatch(given)
  assert json_equal(actual,want),(p,'API wrong result/type',actual,want)
  if new_action=='redact' and p['action']==new_action:
   def mutable_ids(x):
    ids={id(x)} if isinstance(x,(dict,list)) else set()
    for child in x.values() if isinstance(x,dict) else x if isinstance(x,list) else []:ids.update(mutable_ids(child))
    return ids
   assert not mutable_ids(actual)&mutable_ids(given['document']),'aliased input containers'
 assert json_equal(given,original),'mutated input'
 if database:assert json_equal(rows(given),old_expected if error else want),'persistence/atomicity'
 cp=prepare(p)
 proc=subprocess.run([sys.executable,'-B','cli.py'],input=json.dumps(cp),text=True,capture_output=True,timeout=8)
 if error:assert proc.returncode==2 and proc.stderr.strip() and 'Traceback' not in proc.stderr and not proc.stdout.strip(),'CLI error contract'
 else:assert proc.returncode==0 and json_equal(json.loads(proc.stdout),want),(p,'CLI wrong result/type',proc.stdout,proc.stderr)
 if database:assert json_equal(rows(cp),old_expected if error else want),'CLI persistence/atomicity'
check(old_payload,old_expected)
for p,want in cases:check(p,want)
for p in errors:check(p,None,True)
check({'action':'unknown'},None,True)
suite=unittest.defaultTestLoader.discover('.')
assert suite.countTestCases()>=3,'need three discoverable tests'
result=unittest.TextTestRunner(verbosity=1).run(suite)
assert result.wasSuccessful(),'generated tests failed'
readme=pathlib.Path('README.md').read_text()
assert len(readme.split())>=40 and 'cli.py' in readme and new_action in readme,'document new CLI usage'
print('PASS')
'''
TEST_SETUP=''' def prepare(self,p):
  import tempfile,sqlite3,copy,pathlib
  p=copy.deepcopy(p)
  tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);p['db']=str(pathlib.Path(tmp.name)/'stock.db')
  with sqlite3.connect(p['db']) as con:
   con.execute('CREATE TABLE stock(sku TEXT PRIMARY KEY,quantity INTEGER NOT NULL)')
   con.executemany('INSERT INTO stock VALUES (?,?)',[('a',5),('b',2)])
  return p
'''
for i,item in enumerate(ITEMS,1):
 d=R/'tasks'/f'{i:02}-{item["name"]}';src=d/'source';acc=d/'acceptance';src.mkdir(parents=True);acc.mkdir()
 new=ACTIONS[i-1];old=item['old_action'];database=i==4
 base_readme='# '+item['title']+'\n\nExisting action '+old+' is exposed through api.dispatch and python cli.py, accepting one JSON object on stdin and writing one JSON result.\n'
 for name,content in {'domain.py':item['old_code'],'api.py':api(old,new,False),'cli.py':CLI,'README.md':base_readme}.items():(src/name).write_text(content)
 subprocess.run(['git','init','-q',str(src)],check=True);subprocess.run(['git','-C',str(src),'add','.'],check=True);subprocess.run(['git','-C',str(src),'-c','user.name=Fixture Builder','-c','user.email=fixture@example.invalid','commit','-qm','Existing utility behavior'],check=True)
 cases=[(dict(action=new,**p),want) for p,want in item['cases']];errors=[dict(action=new,**p) for p in item['errors']];old_payload=dict(action=old,**item['old_input'])
 data='\n'.join(k+'='+repr(v) for k,v in dict(cases=cases,errors=errors,database=database,new_action=new,old_payload=old_payload,old_expected=item['old_output']).items())
 (acc/'check.py').write_text(ORACLE.replace('HELPER',HELPER).replace('DATA',data))
 task={'repo':'source','objective':item['spec']+COMMON,'acceptance':'acceptance','checks':[['python','-B','-I','/acceptance/check.py']],'max_attempts':3,'max_turns':24,'wall_time_seconds':900}
 (d/'task.json').write_text(json.dumps(task,indent=2)+'\n')
 tests='import unittest\nfrom api import dispatch\n'+HELPER+'class BehaviorTests(unittest.TestCase):\n'
 if database:tests+=TEST_SETUP
 for j,(p,want) in enumerate(cases[:3]):
  expr='self.prepare('+repr(p)+')' if database else repr(p)
  tests+=f' def test_case_{j}(self):\n  self.assertTrue(json_equal(dispatch({expr}),{want!r}))\n'
 if errors:
  expr='self.prepare('+repr(errors[0])+')' if database else repr(errors[0])
  tests+=f' def test_rejected(self):\n  with self.assertRaises(ValueError):dispatch({expr})\n'
 example=dict(cases[0][0])
 if database:example['db']='/tmp/warehouse.db'
 docs=base_readme+'\n'+item['spec']+'\n\nExample (SQLite requires the documented database to already exist):\n\n```sh\nprintf \'%s\\n\' \''+json.dumps(example,ensure_ascii=False)+"' | python cli.py\n```\n\nRun tests with python -m unittest discover. Inputs remain unchanged and failures follow the documented CLI error contract.\n"
 reference={'domain.py':item['old_code']+item['code'],'api.py':api(old,new,True),'cli.py':CLI,'test_behavior.py':tests,'README.md':docs}
 (R/'private'/f'{i:02}-reference.json').write_text(json.dumps(reference,indent=2)+'\n')
amb=R/'ambiguous';(amb/'source').mkdir(parents=True);(amb/'acceptance').mkdir()
for name,c in {'domain.py':"def legacy(p):return [r['id'] for r in p['requests']]\n",'api.py':api('request_ids','allocate',False),'cli.py':CLI,'README.md':'# Refund queue\nrequest_ids lists requests in input order.\n'}.items():(amb/'source'/name).write_text(c)
subprocess.run(['git','init','-q',str(amb/'source')],check=True);subprocess.run(['git','-C',str(amb/'source'),'add','.'],check=True);subprocess.run(['git','-C',str(amb/'source'),'-c','user.name=Fixture Builder','-c','user.email=fixture@example.invalid','commit','-qm','Existing refund queue'],check=True)
(amb/'task.json').write_text(json.dumps({'repo':'source','objective':'Add refund allocation when approved refund claims exceed the available cash budget. Finance has not decided between paying the oldest approved claims in full first or distributing the available budget proportionally among all approved claims. These policies yield different payments; no authoritative choice exists in this repository. Obtain the business owner decision before implementing allocation. Preserve request_ids.','acceptance':'acceptance','checks':[['python','-B','-I','/acceptance/check.py']],'max_attempts':3,'max_turns':24,'wall_time_seconds':900},indent=2)+'\n')
(amb/'acceptance/check.py').write_text("raise AssertionError('Refund policy requires owner input')\n")
(R/'private/ambiguity.json').write_text(json.dumps({'expected_status':'needs_input','question_must_distinguish':['oldest claims paid in full','proportional payments'],'outside_coding_denominator':True},indent=2)+'\n')
(R/'run-budget.json').write_text(json.dumps({'max_attempts':3,'max_turns':24,'wall_time_seconds_per_task':900},indent=2)+'\n')
