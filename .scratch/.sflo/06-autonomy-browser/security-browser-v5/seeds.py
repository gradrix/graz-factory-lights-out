"""Independent seed-reader boundaries; only private files and controlled read hooks."""
import json,os,pathlib,tempfile,time
from unittest.mock import patch
import probe
b=probe.b;rows=[]
# The checkout mount suppresses access-time updates. Use an owned tiny tmpfs
# temporary file to measure an actual atime-only transition, without mocking it.
with tempfile.TemporaryDirectory(prefix='gflo-seed-security-',dir='/dev/shm') as td:
 seed=pathlib.Path(td)/'seed.json';seed.write_bytes(b'{}');os.utime(seed,ns=(time.time_ns()-172800*10**9,time.time_ns()))
 before=seed.stat();data=b.read_seed(seed);after=seed.stat()
 assert data==b'{}' and before.st_atime_ns!=after.st_atime_ns
 assert before.st_mtime_ns==after.st_mtime_ns and before.st_ctime_ns==after.st_ctime_ns
 assert before!=after
 rows.append({'case':'actual-tmpfs-atime-only','accepted':True,'atime_changed':True,'mtime_changed':False,'ctime_changed':False,'old_full_stat_predicate_rejects':before!=after})
cases=['regular','actual-atime','exact65536','oversize65537','symlink','ancestor-link','hardlink','fifo','directory','before-open-replacement','before-open-symlink','before-open-fifo','after-read-write','after-read-truncate','after-read-restore-mtime','after-read-replacement','after-read-parent-replacement','after-read-hardlink','after-read-mode']
for mode in cases:
 with tempfile.TemporaryDirectory(dir=probe.PRIVATE) as td:
  root=pathlib.Path(td);parent=root/'input';parent.mkdir();seed=parent/'seed.json';seed.write_bytes(b'{}')
  if mode=='actual-atime':os.utime(seed,ns=(time.time_ns()-172800*10**9,time.time_ns()))
  if mode=='exact65536':seed.write_bytes(b' '*65534+b'{}')
  if mode=='oversize65537':seed.write_bytes(b' '*65535+b'{}')
  if mode=='symlink':seed.unlink();seed.symlink_to(root/'target');(root/'target').write_bytes(b'{}')
  if mode=='ancestor-link':(root/'alias').symlink_to(parent);seed=root/'alias/seed.json'
  if mode=='hardlink':os.link(seed,root/'alias')
  if mode=='fifo':seed.unlink();os.mkfifo(seed)
  if mode=='directory':seed.unlink();seed.mkdir()
  before=seed.lstat();opened=[];read_sizes=[];mutated=[False];original_open=os.open;original_fdopen=os.fdopen
  def open_hook(path,flags,*args,**kwargs):
   if path=='seed.json' and mode.startswith('before-open-') and not mutated[0]:
    mutated[0]=True;seed.unlink()
    if mode=='before-open-replacement':seed.write_bytes(b'{}')
    elif mode=='before-open-symlink':(root/'target').write_bytes(b'secret');seed.symlink_to(root/'target')
    else:os.mkfifo(seed)
   return original_open(path,flags,*args,**kwargs)
  def change():
   if not mode.startswith('after-read-'):return
   mutated[0]=True
   if mode in ['after-read-write','after-read-restore-mtime']:
    seed.write_bytes(b'[]')
    if mode=='after-read-restore-mtime':os.utime(seed,ns=(before.st_atime_ns,before.st_mtime_ns))
   elif mode=='after-read-truncate':seed.write_bytes(b'')
   elif mode=='after-read-replacement':replacement=parent/'replacement';replacement.write_bytes(b'{}');replacement.replace(seed)
   elif mode=='after-read-parent-replacement':parent.rename(root/'old');parent.mkdir();seed.write_bytes(b'{}')
   elif mode=='after-read-hardlink':os.link(seed,root/'newlink')
   elif mode=='after-read-mode':seed.chmod(0o400)
  class Reader:
   def __init__(self,stream):self.stream=stream
   def __enter__(self):opened.append(True);return self
   def __exit__(self,*args):self.stream.close()
   def fileno(self):return self.stream.fileno()
   def read(self,size):read_sizes.append(size);data=self.stream.read(size);change();return data
  def fdopen_hook(fd,*args,**kwargs):return Reader(original_fdopen(fd,*args,**kwargs))
  error=None;data=None;started=time.monotonic()
  with patch.object(b.os,'open',open_hook),patch.object(b.os,'fdopen',fdopen_hook):
   try:data=b.read_seed(seed)
   except (ValueError,OSError) as e:error=type(e).__name__+': '+str(e)
  after=seed.lstat();expected=mode in ['regular','actual-atime','exact65536'];assert (error is None)==expected,(mode,error)
  if expected:assert len(data)==before.st_size
  if mode.startswith(('before-open-','after-read-')):assert mutated[0]
  assert read_sizes in [[],[65537]],read_sizes
  if mode in ['oversize65537','symlink','ancestor-link','hardlink','fifo','directory','before-open-replacement','before-open-symlink','before-open-fifo']:assert not read_sizes
  rows.append({'case':mode,'accepted':error is None,'error':error,'returned_bytes':len(data) if data is not None else None,'requested_read_sizes':read_sizes,'actual_mutation_performed':mutated[0],'elapsed_s':time.monotonic()-started,'atime_changed':before.st_atime_ns!=after.st_atime_ns,'mtime_changed':before.st_mtime_ns!=after.st_mtime_ns,'ctime_changed':before.st_ctime_ns!=after.st_ctime_ns})
# Public-seam control: selected rejected seed inputs never reach the pair executor.
for mode in ['actual-atime','hardlink','fifo','symlink']:
 with tempfile.TemporaryDirectory(dir=probe.PRIVATE) as td:
  store,approval,executor=probe.fixture(pathlib.Path(td));seed=pathlib.Path(approval['seed']);calls=[]
  def pair(*args,**kwargs):calls.append(True);return executor(*args,**kwargs)
  store.pair=pair
  if mode=='actual-atime':os.utime(seed,ns=(time.time_ns()-172800*10**9,time.time_ns()))
  if mode=='hardlink':os.link(seed,seed.parent/'alias')
  if mode=='fifo':seed.unlink();os.mkfifo(seed)
  if mode=='symlink':seed.unlink();seed.symlink_to(seed.parent/'target');(seed.parent/'target').write_bytes(b'{}')
  error=None;value=None
  try:value=store.check(approval)
  except (ValueError,OSError) as e:error=type(e).__name__+': '+str(e)
  assert bool(calls)==(mode=='actual-atime')
  if mode=='actual-atime':assert value['receipt']['outcome']['status']=='passed'
  else:assert error is not None
  rows.append({'case':'store-'+mode,'pair_calls':len(calls),'error':error,'passed':value['receipt']['outcome']['status'] if value else None})
(probe.OUT/'seed-results.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
