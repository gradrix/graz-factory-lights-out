"""Independent saved-evidence controls; no candidate execution or inference."""
import hashlib,json,pathlib,unittest
TRIAL=pathlib.Path('/home/gradrix/repos/gflo/.gflo/executable-review-protocol-trial-1')
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()
def reconstruct(case):
 """Separate implementation of predecessor feedback, from raw captured bytes."""
 root=TRIAL/case;ledger=json.loads((root/'ledger.json').read_text());rows=[]
 for command in ledger['commands']:
  number=command['number'];folder=root/'commands'/f'{number:02d}';raw=(folder/'stdout.body').read_bytes();start=json.loads((folder/'started.json').read_text());result=json.loads((folder/'result.json').read_text());cleanup=json.loads((folder/'cleanup.json').read_text());creation=json.loads((folder/'creation.json').read_text());prefix=(start['nonce']+'\n').encode();assert raw.startswith(prefix)
  assert hashlib.sha256(raw).hexdigest()==start['stdout_sha256']==command['stdout_sha256']
  auxiliary=result['output'].encode();assert hashlib.sha256(auxiliary).hexdigest()==command['stderr_sha256']
  assert command['status']=='attested'and cleanup['confirmed_absent']is True and cleanup['name']==creation['name']==command['name']
  combined=raw[len(prefix):]+auxiliary;rows.append({'id':number,'command':command['command'],'text':combined[:16384].decode(errors='replace'),'exit_code':result['exit_code'],'timed_out':result['timed_out'],'output_limited':result.get('limited',False)or len(combined)>16384})
 return rows
class SavedEvidenceQA(unittest.TestCase):
 def test_complete_frozen_manifest(self):
  manifest=TRIAL/'artifact-hashes.json';self.assertEqual(hashlib.sha256(manifest.read_bytes()).hexdigest(),'46960c632593785cb5e033dec3126d76fc5bc97206adde8c59450161fef52804');files=json.loads(manifest.read_text());self.assertEqual(len(files),406)
  for name,sha in files.items():self.assertEqual(hashlib.sha256((TRIAL/name).read_bytes()).hexdigest(),sha,name)
 def test_original_shell_success_is_not_suite_success(self):
  rows=reconstruct('case-01');suite=rows[1];self.assertEqual(suite['exit_code'],0);self.assertIn('FAILED (errors=1)',suite['text']);self.assertIn('Ran 11 tests',suite['text']);self.assertNotIn('Ran 11 tests',rows[6]['text'])
 def test_all_captured_feedback_reconstructible(self):
  self.assertEqual([len(reconstruct(f'case-{i:02d}'))for i in range(1,5)],[7,9,5,12])
 def test_prototype_catalog_matches_independent_reconstruction(self):
  import sys,tempfile;sys.path.insert(0,str(pathlib.Path(__file__).parent));import review_evidence_prototype as p
  out=pathlib.Path(tempfile.mkdtemp())/"pkg";repo=pathlib.Path(__file__).resolve().parents[1]
  p.prepare(repo/"evaluations/executable-review/manifest.json",TRIAL/"artifact-hashes.json",out)
  for i in range(1,5):
   case=f"case-{i:02d}";catalog=json.loads((out/case/"payload.json").read_bytes())["catalog"]
   for row in reconstruct(case):
    text="".join(s["text"] for s in catalog["segments"] if s["command_id"]==row["id"]);command=catalog["commands"][row["id"]-1]
    self.assertEqual(text,row["text"]);self.assertEqual((command["command"],command["exit_code"],command["timed_out"],command["output_limited"]),(row["command"],row["exit_code"],row["timed_out"],row["output_limited"]))
if __name__=="__main__":unittest.main(verbosity=2)
