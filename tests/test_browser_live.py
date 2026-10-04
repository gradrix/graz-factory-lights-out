"""Actual fixed-profile checks when approved offline archives/images are installed."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import unittest
from gflo.browser import BrowserStore, BROWSER_IMAGE

ROOT=Path(__file__).resolve().parents[1]

class BrowserLiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archives=ROOT/'.gflo/browser-boundary-prototype'
        if not shutil.which('docker') or not (cls.archives/'playwright.tgz').is_file():
            raise unittest.SkipTest('Approved browser packages not provisioned')
        check=subprocess.run(['docker','image','inspect',BROWSER_IMAGE],capture_output=True,timeout=15)
        if check.returncode:raise unittest.SkipTest('Approved browser image not provisioned')

    def test_five_actual_journeys_and_cancelled_pair(self):
        with tempfile.TemporaryDirectory() as root:
            store=BrowserStore(Path(root)/'store');support=store.prepare(self.archives)['id']
            for case in ['create-reload','validation','edit-cancel','conflict','failed-save-retry']:
                checks=ROOT/'evaluations/local-browser/journeys'/case
                request={'app':str(ROOT/'evaluations/local-browser/app'),'checks':str(checks),'seed':str(checks/'seed.json'),'case':case,'support':support}
                with self.subTest(case=case):
                    saved=store.check(request)
                    result=saved['receipt']
                    self.assertEqual(result['outcome']['status'],'passed',result['outcome'])
                    self.assertTrue(result['executor']['facts']['cleanup']['confirmed'])
                    self.assertGreater(result['outcome']['runtime']['shm']['peakBytes'],0)
                    self.assertIn('trace.zip',result['artifacts'])
                    if case=='conflict':
                        import io,zipfile
                        with zipfile.ZipFile(store.root/saved['id']/'artifacts'/'trace.zip') as outer:
                            self.assertEqual(set(outer.namelist()),{'manifest.json','context-1.zip','context-2.zip'})
                            with zipfile.ZipFile(io.BytesIO(outer.read('context-2.zip'))) as inner:
                                trace=b'\n'.join(inner.read(name) for name in inner.namelist() if name.endswith('.trace'))
                                self.assertIn(b'Second',trace)
                                self.assertIn(b'Reserve',trace)
                                self.assertIn(b'click',trace)
            checks=Path(root)/'hang';checks.mkdir();(checks/'journey.cjs').write_text('module.exports=async()=>{await new Promise(()=>{})}')
            request.update(checks=str(checks),case='cancel')
            started=time.monotonic()
            with self.assertRaisesRegex(ValueError,'cancelled'):
                store.check(request,cancelled=lambda:time.monotonic()-started>2)
            remaining=subprocess.check_output(['docker','ps','-aq','--filter','label=gflo.browser='+store.label],text=True)
            self.assertEqual(remaining.strip(),'')
            self.assertLess(time.monotonic()-started,15)

    def test_app_death_is_not_success(self):
        with tempfile.TemporaryDirectory() as root:
            root=Path(root);store=BrowserStore(root/'store');support=store.prepare(self.archives)['id']
            app=root/'app';app.mkdir();(app/'server.cjs').write_text('process.exit(0)')
            checks=ROOT/'evaluations/local-browser/journeys/create-reload'
            result=store.check({'app':str(app),'checks':str(checks),'seed':str(checks/'seed.json'),'case':'app-death','support':support})['receipt']
            self.assertEqual(result['outcome']['status'],'failed')
            self.assertIn('Application exited',result['executor']['facts']['failure']['message'])
            self.assertTrue(result['executor']['facts']['cleanup']['confirmed'])

    def test_context_limit_is_enforced_for_concurrent_creation(self):
        with tempfile.TemporaryDirectory() as root:
            root=Path(root);store=BrowserStore(root/'store');support=store.prepare(self.archives)['id']
            checks=root/'checks';checks.mkdir()
            (checks/'journey.cjs').write_text("module.exports=async({page,baseURL,newContext,screenshot})=>{await page.goto(baseURL);await Promise.all([newContext(),newContext(),newContext(),newContext()]);await screenshot()}")
            result=store.check({'app':str(ROOT/'evaluations/local-browser/app'),'checks':str(checks),'seed':str(ROOT/'evaluations/local-browser/journeys/create-reload/seed.json'),'case':'context-cap','support':support})['receipt']
            self.assertEqual(result['outcome']['status'],'failed')
            self.assertIn('context limit',result['outcome']['failure']['message'])

    def test_exact_origin_blocks_redirect_hops_and_websockets(self):
        with tempfile.TemporaryDirectory() as root:
            root=Path(root);store=BrowserStore(root/'store');support=store.prepare(self.archives)['id']
            app=root/'app';app.mkdir()
            (app/'server.cjs').write_text(r'''const http=require('http'),crypto=require('crypto');let hits=[];
const side=http.createServer((q,r)=>{hits.push(q.url);r.setHeader('Access-Control-Allow-Origin','*');r.end('side')});
side.on('upgrade',(q,s)=>{hits.push('ws:'+q.url);const accept=crypto.createHash('sha1').update(q.headers['sec-websocket-key']+'258EAFA5-E914-47DA-95CA-C5AB0DC85B11').digest('base64');s.write('HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: '+accept+'\r\n\r\n')});side.listen(3211,'127.0.0.1');
http.createServer((q,r)=>{if(q.url==='/health')return r.end('ok');if(q.url==='/hits'){r.setHeader('Content-Type','application/json');return r.end(JSON.stringify(hits))}if(q.url==='/redirect'){r.writeHead(302,{Location:'http://127.0.0.1:3211/side'});return r.end()}if(q.url==='/local-redirect'){r.writeHead(302,{Location:'/'});return r.end()}r.setHeader('Content-Type','text/html');r.end('<!doctype html><h1>Owned</h1>')}).listen(3210,'127.0.0.1');''')
            seed=root/'seed.json';seed.write_text('{}')
            cases={
                'control':"await page.evaluate(async()=>{await fetch('/health')})",
                'redirect-fetch':"await page.evaluate(async()=>{try{await fetch('/redirect')}catch{}})",
                'redirect-navigation':"try{await page.goto(baseURL+'/redirect')}catch{}",
                'local-redirect':"await page.evaluate(async()=>{try{await fetch('/local-redirect')}catch{}})",
                'websocket':"await page.evaluate(()=>new Promise(resolve=>{const socket=new WebSocket('ws://127.0.0.1:3211/ws');socket.onopen=()=>{socket.close();resolve()};socket.onerror=()=>resolve();socket.onclose=()=>resolve();setTimeout(resolve,1000)}))"}
            for name,action in cases.items():
                checks=root/name;checks.mkdir()
                (checks/'journey.cjs').write_text("module.exports=async({page,baseURL,request,screenshot})=>{await page.goto(baseURL);"+action+";await page.waitForTimeout(100);const hits=await(await request.get(baseURL+'/hits')).json();require('assert/strict').deepEqual(hits,[]);console.error('CHECK_DIAGNOSTIC');await screenshot()}")
                with self.subTest(case=name):
                    saved=store.check({'app':str(app),'checks':str(checks),'seed':str(seed),'case':name,'support':support})
                    result=saved['receipt']
                    self.assertEqual(result['outcome']['status'],'passed' if name=='control' else 'failed')
                    if name!='control':
                        self.assertNotIn('AssertionError',result['outcome']['failure']['message'])
                    self.assertTrue(result['executor']['facts']['cleanup']['confirmed'])
                    for container in result['executor']['facts']['containers'].values():
                        self.assertEqual(container['host']['LogConfig']['Type'],'none')
                    self.assertIn('CHECK_DIAGNOSTIC',result['executor']['diagnostics'])

    def test_readiness_does_not_follow_health_redirect(self):
        with tempfile.TemporaryDirectory() as root:
            root=Path(root);store=BrowserStore(root/'store');support=store.prepare(self.archives)['id']
            app=root/'app';app.mkdir()
            (app/'server.cjs').write_text("const http=require('http');http.createServer((q,r)=>{console.error('UNAPPROVED_HEALTH_CONTACT');r.end('ok')}).listen(3211,'127.0.0.1');http.createServer((q,r)=>{r.writeHead(302,{Location:'http://127.0.0.1:3211/health'});r.end()}).listen(3210,'127.0.0.1')")
            checks=ROOT/'evaluations/local-browser/journeys/create-reload'
            saved=store.check({'app':str(app),'checks':str(checks),'seed':str(checks/'seed.json'),'case':'redirect-health','support':support})
            result=saved['receipt']
            self.assertEqual(result['outcome']['status'],'failed')
            self.assertIn('readiness deadline',result['outcome']['failure']['message'])
            self.assertNotIn('UNAPPROVED_HEALTH_CONTACT',result['executor']['diagnostics'])
            self.assertTrue(result['executor']['facts']['cleanup']['confirmed'])

    def test_owner_death_recovery_has_private_facts_under_common_umasks(self):
        import os,sys,stat
        for mask in [0o002,0o077]:
            with self.subTest(umask=oct(mask)),tempfile.TemporaryDirectory() as root:
                root=Path(root);store=BrowserStore(root/'store');support=store.prepare(self.archives)['id']
                checks=root/'checks';checks.mkdir();(checks/'journey.cjs').write_text('module.exports=async()=>{await new Promise(()=>{})}')
                approval={'app':str(ROOT/'evaluations/local-browser/app'),'checks':str(checks),'seed':str(ROOT/'evaluations/local-browser/journeys/create-reload/seed.json'),'case':'owner-umask','support':support}
                script="import os,json,sys; from gflo.browser import BrowserStore; os.umask(int(sys.argv[1])); BrowserStore(sys.argv[2]).check(json.loads(sys.argv[3]))"
                owner=subprocess.Popen([sys.executable,'-c',script,str(mask),str(store.root),json.dumps(approval)],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
                try:
                    deadline=time.monotonic()+20
                    while time.monotonic()<deadline:
                        running=subprocess.check_output(['docker','ps','-q','--filter','label=gflo.browser='+store.label],text=True).split()
                        if len(running)==2:break
                        if owner.poll() is not None:self.fail(owner.stderr.read().decode())
                        time.sleep(.05)
                    self.assertEqual(len(running),2)
                    owner.kill();owner.wait(timeout=5)
                    deadline=time.monotonic()+20
                    while time.monotonic()<deadline:
                        remaining=subprocess.check_output(['docker','ps','-aq','--filter','label=gflo.browser='+store.label],text=True).split()
                        facts=list(store.root.glob('.work-*/facts.json'))
                        if not remaining and facts:
                            try:json.loads(facts[0].read_bytes());break
                            except (json.JSONDecodeError,OSError):pass
                        time.sleep(.05)
                    self.assertFalse(remaining)
                    self.assertEqual(len(facts),1)
                    self.assertEqual(stat.S_IMODE(facts[0].stat().st_mode),0o600)
                    store.cleanup()
                    self.assertFalse((store.root/'.cleanup-required').exists())
                    self.assertFalse(list(store.root.glob('.work-*')))
                finally:
                    if owner.poll() is None:owner.kill();owner.wait(timeout=5)
                    owner.stderr.close()
