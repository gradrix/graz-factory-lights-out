#!/usr/bin/env python3
"""Independent frozen browser fixture controls; explicit --run required."""
import argparse,hashlib,io,json,os,pathlib,shutil,sys,time,zipfile

sha=lambda b:hashlib.sha256(b).hexdigest()
def read(path):return json.loads(pathlib.Path(path).read_text())

def trace_audit(path,expected_contexts):
    """Bounded in-memory inspection only; never extract archives to host or render HTML."""
    assert path.stat().st_size<=16*1024*1024
    with zipfile.ZipFile(path) as archive:
        entries=archive.infolist();assert len(entries)==expected_contexts+1
        assert {e.filename for e in entries}=={'manifest.json',*[f'context-{i}.zip' for i in range(1,expected_contexts+1)]}
        assert all(e.file_size<=16*1024*1024 for e in entries)
        info=archive.getinfo('manifest.json');assert info.file_size<=8192
        manifest=json.loads(archive.read(info));assert len(manifest['contexts'])==expected_contexts
        summaries=[]
        for item in manifest['contexts']:
            data=archive.read(item['name']);assert sha(data)==item['sha256'] and len(data)==item['size']
            with zipfile.ZipFile(io.BytesIO(data)) as inner:
                members=inner.infolist();assert len(members)<=2048
                tracefiles=[m for m in members if m.filename.endswith('.trace')]
                assert tracefiles and sum(m.file_size for m in tracefiles)<=16*1024*1024
                calls=[]
                for member in tracefiles:
                    for line in inner.read(member).splitlines():
                        assert len(line)<=1024*1024
                        event=json.loads(line)
                        if event.get('type')=='before':calls.append({'method':event.get('method'),'params':event.get('params',{})})
                assert any(c['method']=='goto' for c in calls), 'Context lacks recorded navigation'
                summaries.append({'context':item['context'],'name':item['name'],'sha256':item['sha256'],'calls':calls})
        if expected_contexts==2:
            calls=summaries[1]['calls']
            assert any(c['method']=='fill' and c['params'].get('value')=='Second' for c in calls),'Second-session reference entry missing'
            assert any(c['method']=='click' and 'Reserve' in str(c['params'].get('selector','')) for c in calls),'Second-session reserve click missing'
        return {'manifest':manifest,'contexts':summaries}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for option in ['repo','candidate','fixture','support-store','output']:p.add_argument('--'+option,type=pathlib.Path,required=True)
    for option in ['candidate-sha256','fixture-sha256','support-id']:p.add_argument('--'+option,required=True)
    p.add_argument('--run',action='store_true');a=p.parse_args()
    if not a.run:p.error('No execution without --run and final frozen candidate')
    repo=a.repo.resolve();fixture=a.fixture.resolve();output=a.output.resolve()
    assert not output.exists(),'Preserve prior output; choose fresh directory'
    output.mkdir(parents=True,mode=0o700);rows=[];summary={'candidate_manifest':a.candidate_sha256,'fixture_manifest':a.fixture_sha256,'support_id':a.support_id,'rows':rows,'status':'running'}
    def save():(output/'results.json').write_text(json.dumps(summary,indent=2)+'\n')
    def frozen():
        assert sha(a.candidate.read_bytes())==a.candidate_sha256
        for name,h in read(a.candidate)['files'].items():assert sha((repo/name).read_bytes())==h,name
        assert sha((fixture/'manifest.json').read_bytes())==a.fixture_sha256
        for name,h in read(fixture/'manifest.json')['files'].items():assert sha((fixture/name).read_bytes())==h,name
    def support_files(root):return {str(p.relative_to(root)):sha(p.read_bytes()) for p in sorted(root.rglob('*')) if p.is_file()}
    save();started=time.monotonic()
    try:
        frozen();sys.path.insert(0,str(repo));from gflo.browser import BrowserStore
        source=BrowserStore(a.support_store);support=source.inspect(a.support_id);assert support['receipt']['kind']=='support'
        supportroot=source.root/a.support_id;before=support_files(supportroot);store=BrowserStore(output/'store');shutil.copytree(supportroot,store.root/a.support_id)
        assert store.inspect(a.support_id)==support;summary['support_receipt']=support;save()
        source_code=(fixture/'app/server.cjs').read_text()
        transforms={
          'create-reload':('else reservations.push(', 'else void('),
          'validation':("if(delta>stock)return send(409,{error:'Not enough stock; remaining inventory refreshed'});", "if(delta>stock){stock--;return send(409,{error:'Not enough stock; remaining inventory refreshed'});}"),
          'edit-cancel':('const delta=value.quantity-previous','const delta=value.quantity'),
          'conflict':('if(delta>stock)','if(false&&delta>stock)'),
          'failed-save-retry':('if(failSave){failSave=false;','if(failSave){stock-=delta;failSave=false;')}
        for mutant in [False,True]:
            for case in read(fixture/'manifest.json')['cases']:
                frozen();assert support_files(supportroot)==before
                label=case+('-mutant' if mutant else '-control');root=output/'inputs'/label;root.mkdir(parents=True)
                shutil.copytree(fixture/'app',root/'app');shutil.copytree(fixture/'journeys'/case,root/'checks')
                shutil.copyfile(fixture/'journeys'/case/'seed.json',root/'seed.json')
                if mutant:
                    old,new=transforms[case];assert source_code.count(old)==1,(case,'mutation not exact')
                    (root/'app/server.cjs').write_text(source_code.replace(old,new))
                request={'app':str(root/'app'),'checks':str(root/'checks'),'seed':str(root/'seed.json'),'case':label,'support':a.support_id}
                (root/'request.json').write_text(json.dumps(request,indent=2)+'\n');row={'case':case,'mutant':mutant,'request':str(root/'request.json')};rows.append(row);save();then=time.monotonic()
                result=store.check(request);row.update(id=result['id'],elapsed_s=time.monotonic()-then);receipt=result['receipt'];(output/(label+'-receipt.json')).write_text(json.dumps(result,indent=2)+'\n')
                assert store.inspect(result['id'])==result
                outcome=receipt['outcome'];row['outcome']=outcome['status'];row['failure']=outcome.get('failure');assert receipt['executor']['facts']['cleanup']['confirmed'] is True
                if mutant:
                    assert outcome['status']=='failed' and outcome.get('failure',{}).get('phase')=='journey','Mutant must fail journey assertions, not unrelated startup/artifact failure'
                else:
                    assert outcome['status']=='passed',(case,outcome.get('failure'))
                    assert 'screen-1.png' in receipt['artifacts'] and 'trace.zip' in receipt['artifacts']
                    expected=2 if case=='conflict' else 1
                    audit=trace_audit(store.root/result['id']/'artifacts/trace.zip',expected)
                    assert audit['manifest']['contexts']==outcome['runtime']['traces']
                    (output/(label+'-trace-audit.json')).write_text(json.dumps(audit,indent=2)+'\n');row['contexts_traced']=expected
                row['expected_outcome_confirmed']=True;save()
                frozen();assert support_files(supportroot)==before and support_files(store.root/a.support_id)==before
        summary['status']='passed_fixture_controls_not_full_product_acceptance'
    except Exception as e:
        summary['status']='failed';summary['error']=type(e).__name__+': '+str(e)[:4096]
    finally:
        summary['elapsed_s']=time.monotonic()-started
        try:frozen();summary['final_input_hashes_match']=True
        except Exception:summary['final_input_hashes_match']=False;summary['status']='failed'
        if 'before' in locals():
            try:
                assert support_files(supportroot)==before
                assert support_files(store.root/a.support_id)==before
                assert source.inspect(a.support_id)==support and store.inspect(a.support_id)==support
                summary['final_support_matches']=True
            except Exception:summary['final_support_matches']=False;summary['status']='failed'
        save()
    print(json.dumps({'status':summary['status'],'results':str(output/'results.json'),'completed':sum(r.get('expected_outcome_confirmed',False) for r in rows)},indent=2))
    return 0 if summary['status'].startswith('passed_') else 1
if __name__=='__main__':raise SystemExit(main())
