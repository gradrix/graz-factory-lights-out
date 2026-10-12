import json,subprocess,pathlib,os
root=pathlib.Path.home()/'benchmark-5090';root.mkdir(exist_ok=True)
c=json.loads(subprocess.check_output(['docker','inspect','local-vllm']))[0]
private=root/'original-container.private.json';private.touch(mode=0o600);private.write_text(json.dumps(c,indent=2));private.chmod(0o600)
report={k:c[k] for k in ['Id','Image','Created']}
report['config']={k:c['Config'][k] for k in ['Image','Entrypoint','Cmd','Labels']}
report['mounts']=c['Mounts'];report['restart']=c['HostConfig']['RestartPolicy'];report['ports']=c['HostConfig']['PortBindings']
report['gpu']=subprocess.check_output(['/usr/lib/wsl/lib/nvidia-smi','-q'],text=True)
report['memory']=subprocess.check_output(['free','-h'],text=True)
report['cpu']=subprocess.check_output(['lscpu'],text=True)
report['date']=subprocess.check_output(['date','-Iseconds'],text=True)
(root/'inventory.json').write_text(json.dumps(report,indent=2))
print('Saved sanitized inventory and private local restore metadata')
