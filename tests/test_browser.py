import io
import json
from pathlib import Path
import tempfile
import unittest
from gflo.browser import BrowserStore, snapshot

class BrowserTests(unittest.TestCase):
    def test_snapshot_freezes_and_rejects_links(self):
        with tempfile.TemporaryDirectory() as root:
            root=Path(root);source=root/'source';source.mkdir();(source/'server.cjs').write_text('server')
            target=root/'frozen'
            identity=snapshot(source,target,256,4*1024*1024)
            self.assertEqual(len(identity),64)
            self.assertEqual((target/'server.cjs').read_text(),'server')
            (source/'link').symlink_to('server.cjs')
            with self.assertRaises(ValueError):snapshot(source,root/'bad',256,4*1024*1024)

    def test_cli_browser_inspect_is_offline(self):
        from unittest.mock import patch
        from gflo.__main__ import main
        with patch('gflo.__main__.BrowserStore') as store,patch('sys.stdout',new_callable=io.StringIO):
            store.return_value.inspect.return_value={'id':'a'*64}
            self.assertEqual(main(['browser','inspect','a'*64]),0)

class BrowserStoreTests(unittest.TestCase):
    def setUp(self):
        import tarfile
        from unittest.mock import patch
        from gflo.browser import digest
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.archives=self.root/'archives';self.archives.mkdir()
        pins={}
        for name in ['playwright','playwright-core']:
            archive=self.archives/(name+'.tgz')
            with tarfile.open(archive,'w:gz') as stream:
                data=b'{"version":"1.63.0"}';info=tarfile.TarInfo('package/package.json');info.size=len(data);stream.addfile(info,io.BytesIO(data))
            pins[name]=digest(archive.read_bytes())
        self.images=patch('gflo.browser.installed_images',return_value={});self.images.start();self.addCleanup(self.images.stop)
        self.pins=patch('gflo.browser.PACKAGES',pins);self.pins.start();self.addCleanup(self.pins.stop)
        self.store=BrowserStore(self.root/'store',executor=self.executor)
        self.support=self.store.prepare(self.archives)['id']
        self.app=self.root/'app';self.app.mkdir();(self.app/'server.cjs').write_text('server')
        self.checks=self.root/'checks';self.checks.mkdir();(self.checks/'journey.cjs').write_text('check')
        self.seed=self.root/'seed.json';self.seed.write_text('{}')
        self.approval={'app':str(self.app),'checks':str(self.checks),'seed':str(self.seed),'support':self.support,'case':'test'}
        self.spec=None

    @staticmethod
    def framed(status='passed'):
        import struct,hashlib
        files={'screen-1.png':b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'+struct.pack('>II',1280,800),
               'trace.zip':b'PK\x03\x04opaque','events.json':b'[]'}
        value={'status':status,'files':[{'name':n,'size':len(d),'sha256':hashlib.sha256(d).hexdigest()} for n,d in files.items()]}
        return json.dumps(value).encode()+b'\n'+b''.join(files.values())

    def executor(self,spec,output,**kwargs):
        self.spec=spec;output.write(self.framed())
        return {'exit_code':0,'reason':None,'diagnostics':'','transport_errors':[],'facts':{'cleanup':{'confirmed':True},'failure':None}}

    def test_check_freezes_and_offline_inspect_detects_artifact_tamper(self):
        record=self.store.check(self.approval)
        self.assertEqual(record['receipt']['outcome']['status'],'passed')
        self.assertIn('OWNED_APP',self.spec['browser_args'])
        self.assertEqual(self.spec['app_args'][self.spec['app_args'].index('--network')+1],'none')
        self.assertIn('NODE_PATH=/support',self.spec['browser_args'])
        for key in ['app_args','browser_args']:
            args=self.spec[key]
            self.assertEqual(args[args.index('--log-driver')+1],'none')
        self.store.pair=lambda *a,**k:self.fail('Offline inspect executed a pair')
        self.assertEqual(self.store.inspect(record['id'])['id'],record['id'])
        path=self.store.root/record['id']/'artifacts'/'trace.zip';path.chmod(0o600);path.write_bytes(b'bad');path.chmod(0o444)
        with self.assertRaises(ValueError):self.store.inspect(record['id'])

    def test_support_tamper_rejected_before_launch(self):
        path=self.store.root/self.support/'support'/'playwright'/'package.json';path.chmod(0o600);path.write_text('{}');path.chmod(0o444)
        with self.assertRaises(ValueError):self.store.check(self.approval)
        self.assertIsNone(self.spec)

    def test_incomplete_artifacts_are_saved_as_failure(self):
        original=self.executor
        def broken(spec,output,**kw):
            result=original(spec,io.BytesIO(),**kw);output.write(b'partial');return result
        self.store.pair=broken;record=self.store.check(self.approval)
        self.assertEqual(record['receipt']['outcome']['status'],'failed')
        self.assertEqual(record['receipt']['artifacts'],{})

    def test_uncertain_cleanup_never_publishes_and_fences_next_check(self):
        original=self.executor
        def broken(*args,**kw):
            result=original(*args,**kw);result['facts']['cleanup']['confirmed']=False;return result
        self.store.pair=broken
        with self.assertRaises(RuntimeError):self.store.check(self.approval)
        self.assertEqual(len([p for p in self.store.root.iterdir() if len(p.name)==64]),1)
        self.assertTrue((self.store.root/'.failure.json').exists())
        with self.assertRaisesRegex(ValueError,'recovery'):self.store.check(self.approval)
        from unittest.mock import patch
        with patch('subprocess.run') as run:
            run.return_value.stdout='';self.store.cleanup()
        self.store.pair=self.executor;self.assertEqual(self.store.check(self.approval)['receipt']['outcome']['status'],'passed')

    def test_owner_or_guardian_exception_retains_fence(self):
        def broken(*args,**kw):raise RuntimeError('guardian missing')
        self.store.pair=broken
        with self.assertRaises(RuntimeError):self.store.check(self.approval)
        self.assertTrue((self.store.root/'.cleanup-required').exists())
        with self.assertRaises(ValueError):self.store.prepare(self.archives)

    def test_failed_commit_preserves_prior_result(self):
        from unittest.mock import patch
        record=self.store.check(self.approval)
        with patch('gflo.browser.sync_directory',side_effect=OSError('sync failed')),self.assertRaises(OSError):self.store.check(self.approval)
        self.assertEqual(self.store.inspect(record['id'])['id'],record['id'])
        self.assertFalse(any(p.name.startswith('.stage-') for p in self.store.root.iterdir()))

    def test_request_bounds_and_missing_entry_fail_before_launch(self):
        for change in [{'case':'../bad'},{'other':True},{'support':'../x'}]:
            with self.subTest(change=change),self.assertRaises(ValueError):self.store.check(dict(self.approval,**change))
        (self.app/'server.cjs').unlink()
        with self.assertRaises(ValueError):self.store.check(self.approval)
        self.assertIsNone(self.spec)

    def test_seed_bounds_and_cancel_before_launch(self):
        self.seed.write_text('x'*65537)
        with self.assertRaises(ValueError):self.store.check(self.approval)
        self.seed.write_text('{}')
        with self.assertRaises(ValueError):self.store.check(self.approval,cancelled=lambda:True)
        self.assertIsNone(self.spec)


    def test_cancellation_during_final_sync_cannot_publish_pass(self):
        from unittest.mock import patch
        from gflo.browser import sync_directory
        cancelled=[False]
        def sync(path):
            sync_directory(path);cancelled[0]=True
        before={p.name for p in self.store.root.iterdir() if len(p.name)==64}
        with patch('gflo.browser.sync_directory',side_effect=sync),self.assertRaises(ValueError):
            self.store.check(self.approval,cancelled=lambda:cancelled[0])
        self.assertEqual({p.name for p in self.store.root.iterdir() if len(p.name)==64},before)


    def test_uncertain_create_requires_explicit_ack_and_preserves_failure(self):
        from unittest.mock import patch
        original=self.executor
        def uncertain(*args,**kwargs):
            result=original(*args,**kwargs)
            result['exit_code']=125
            result['facts']['cleanup']={'confirmed':False,'uncertain_creates':['owned-app']}
            return result
        self.store.pair=uncertain
        with self.assertRaises(RuntimeError):self.store.check(self.approval)
        original_failure=json.loads((self.store.root/'.failure.json').read_bytes())
        with patch('gflo.browser.subprocess.run') as run:
            run.return_value.stdout=''
            with self.assertRaisesRegex(ValueError,'acknowledge-create-uncertainty'):self.store.cleanup()
            self.assertTrue((self.store.root/'.cleanup-required').exists())
            self.store.cleanup(acknowledge_create_uncertainty=True)
        recovery=[self.store.inspect(path.name)['receipt'] for path in self.store.root.iterdir() if len(path.name)==64]
        recovery=next(receipt for receipt in recovery if receipt['kind']=='recovery')
        self.assertTrue(recovery['operator_acknowledged_create_uncertainty'])
        self.assertEqual(recovery['original_failure_evidence']['.failure.json']['value'],original_failure)
        self.assertIn('not proof',recovery['daemon_readback'])
        self.store.pair=self.executor
        self.assertEqual(self.store.check(self.approval)['receipt']['outcome']['status'],'passed')


class BrowserArtifactTests(unittest.TestCase):
    def test_fixed_transport_rejects_extra_duplicate_oversize_corrupt_and_dimensions(self):
        import hashlib
        from gflo.browser import receive
        for name,size,data in [('evil/../file',1,b'x'),('screen-1.png',2*1024*1024+1,b'x'),('screen-1.png',1,b'x'),('trace.zip',4,b'xxxx'),('events.json',2,b'{}')]:
            value={'status':'passed','files':[{'name':name,'size':size,'sha256':hashlib.sha256(data).hexdigest()}]}
            with tempfile.TemporaryDirectory() as root,self.subTest(name=name,size=size),self.assertRaises(ValueError):
                receive(io.BytesIO(json.dumps(value).encode()+b'\n'+data),Path(root)/'artifacts')
        for raw in [b'no newline',b'x'*65537,BrowserStoreTests.framed()+b'extra',BrowserStoreTests.framed()[:-1],b'{"status":"passed","files":[]}\n']:
            with tempfile.TemporaryDirectory() as root,self.assertRaises(ValueError):receive(io.BytesIO(raw),Path(root)/'artifacts')

class BrowserInputPolicyTests(unittest.TestCase):
    def test_snapshot_caps_and_unsafe_store(self):
        with tempfile.TemporaryDirectory() as root:
            root=Path(root);source=root/'source';source.mkdir();(source/'file').write_bytes(b'12345')
            for entries,size in [(0,10),(2,4)]:
                with self.assertRaises(ValueError):snapshot(source,root/('copy'+str(entries)),entries,size)
            public=root/'public';public.mkdir(mode=0o755)
            with self.assertRaises(ValueError):BrowserStore(public)
            link=root/'link';link.symlink_to(source)
            with self.assertRaises(ValueError):BrowserStore(link)
            store=BrowserStore(root/'store')
            with store.locked(),self.assertRaises(ValueError):
                with store.locked():pass

    def test_offline_archive_digest_and_types_are_checked(self):
        import tarfile,hashlib
        from gflo.browser import support_archive
        with tempfile.TemporaryDirectory() as root:
            root=Path(root);archive=root/'a.tgz'
            with tarfile.open(archive,'w:gz') as tar:
                item=tarfile.TarInfo('package/link');item.type=tarfile.SYMTYPE;item.linkname='/etc/passwd';tar.addfile(item)
            with self.assertRaises(ValueError):support_archive(archive,root/'bad','0'*64)
            with self.assertRaises(ValueError):support_archive(archive,root/'bad',hashlib.sha256(archive.read_bytes()).hexdigest())

    def test_directory_enumeration_stops_at_entry_budget(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as root:
            source=Path(root)/'source';source.mkdir()
            def too_many(path,pattern):
                for index in range(3):yield path/str(index)
                raise AssertionError('Enumerated beyond rejection budget')
            with patch.object(Path,'rglob',too_many),self.assertRaises(ValueError):
                snapshot(source,Path(root)/'copy',2,1024)

    def test_missing_or_wrong_images_fail_without_pull(self):
        from unittest.mock import patch
        from gflo.browser import installed_images
        with patch('gflo.browser.subprocess.run') as run:
            run.return_value.returncode=1
            with self.assertRaises(ValueError):installed_images()
            self.assertNotIn('pull',run.call_args.args[0])
            run.return_value.returncode=0;run.return_value.stdout='[{"Id":"wrong","Architecture":"amd64","Os":"linux"}]'
            with self.assertRaises(ValueError):installed_images()
