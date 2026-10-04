#!/usr/bin/env python3
"""Prepare disposable conforming controls; does not import or execute candidates.
Each output is a fresh sibling copy, never an in-place edit. Run the unchanged
qa-manifest-probes.py against original and control under identical container settings.
"""
import argparse,hashlib,json,pathlib,re,shutil

def hashes(root):
 return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(root.rglob('*'))if p.is_file()}
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--arm',type=int,choices=[1,2],required=True);parser.add_argument('--source',type=pathlib.Path,required=True);parser.add_argument('--output',type=pathlib.Path,required=True);args=parser.parse_args()
 source=args.source.resolve();output=args.output.absolute()
 assert source.is_dir()and not output.exists()and not output.resolve().is_relative_to(source)
 assert not any(p.is_symlink()for p in source.rglob('*'))
 before=hashes(source);shutil.copytree(source,output)
 if args.arm==1:
  path=output/'tests/test_manifest_tool.py';text=path.read_text();old="[ 'python', 'main.py' ]";assert text.count(old)==1
  # Preserve all assertions. Resolve main.py from this copied test's location;
  # no /workspace assumption and no substitution of expected results.
  text=text.replace('import subprocess\n','import subprocess\nimport sys\nfrom pathlib import Path\n')
  text=text.replace(old,"[sys.executable, str(Path(__file__).resolve().parents[1] / 'main.py')]")
  assert text.count("cwd='/workspace'")==1;text=text.replace("cwd='/workspace'","cwd='/tmp'");path.write_text(text)
 else:
  path=output/'README.md';text=path.read_text();matches=list(re.finditer(r'"sha256": "([ab]+)"',text));assert [len(m.group(1))for m in matches]==[62,60,62,60]
  # Keep paths, sizes, signatures and documented expected response unchanged.
  text=re.sub(r'("sha256": ")([ab]+)(")',lambda m:m.group(1)+m.group(2)[0]*64+m.group(3),text);path.write_text(text)
 after=hashes(output);assert hashes(source)==before
 changed=[name for name in before if before[name]!=after[name]]
 assert changed==(['tests/test_manifest_tool.py']if args.arm==1 else ['README.md'])
 receipt={'arm':args.arm,'source':str(source),'control':str(output),'source_unchanged':True,'changed':changed,'original_files':before,'control_files':after,'purpose':'Synthetic conforming control only; never re-score actual arm'}
 (output.parent/(output.name+'-control.json')).write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'control':str(output),'changed':changed,'source_unchanged':True}))
if __name__=='__main__':main()
