import sys, unittest, pathlib, shutil, os, json, subprocess
sys.path.insert(0,'/workspace')
from api import dispatch
kind=sys.argv[1]
if kind=='03':
 # Regression control: required default discovery passes with the delivered marker.
 suite=unittest.defaultTestLoader.discover('/workspace');assert suite.countTestCases()>=3
 assert unittest.TextTestRunner().run(suite).wasSuccessful()
 # Recreate the precise old packaging defect in disposable sandbox storage.
 shutil.copytree('/workspace','/tmp/without-marker')
 pathlib.Path('/tmp/without-marker/tests/__init__.py').unlink()
 p=subprocess.run([sys.executable,'-B','-c',"import unittest;assert unittest.defaultTestLoader.discover('.').countTestCases()>=3"],cwd='/tmp/without-marker',capture_output=True,text=True)
 assert p.returncode!=0 and 'AssertionError' in p.stderr
 print('fixed discovery passes; removal of marker is rejected')
else:
 import domain
 # Independent checker based on left-index parity and decimal digit sum.
 def valid(s):
  total=sum(sum(map(int,str(int(c)*(2 if i%2==len(s)%2 else 1)))) for i,c in enumerate(s))
  return bool(s) and total%10==0
 for n in range(1000):
  digits=str(n).zfill(3)
  candidates=[digits+str(d) for d in range(10) if valid(digits+str(d))];assert len(candidates)==1
  assert dispatch({'action':'append','number':digits})==candidates[0]
  for d in range(10):assert dispatch({'action':'check','number':digits+str(d)})==valid(digits+str(d))
 for payload,expected in [({'action':'append','number':'4992 781'},'49927817'),({'action':'check','number':'4992 781-7'},True)]:
  p=subprocess.run([sys.executable,'-B','cli.py'],input=json.dumps(payload),capture_output=True,text=True);assert p.returncode==0 and json.loads(p.stdout)==expected
 p=subprocess.run([sys.executable,'-B','cli.py'],input=json.dumps({'action':'append','number':'- -'}),capture_output=True,text=True);assert p.returncode==2 and p.stderr.strip() and not p.stdout
 suite=unittest.defaultTestLoader.discover('/workspace');assert unittest.TextTestRunner().run(suite).wasSuccessful()
 # Negative control: a checksum function that falsely validates every number.
 domain._luhn_sum=lambda digits:0
 suite=unittest.defaultTestLoader.discover('/workspace');result=unittest.TextTestRunner().run(suite);assert not result.wasSuccessful()
 print('1000 append/10000 check controls and README examples pass; broken checksum mutant rejected')
