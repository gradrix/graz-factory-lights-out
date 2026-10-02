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
            result=store.check(request,cancelled=lambda:time.monotonic()-started>2)['receipt']
            self.assertEqual(result['outcome']['status'],'failed')
            self.assertTrue(result['executor']['facts']['cleanup']['confirmed'])
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
