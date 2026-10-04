"""Controlled daemon completion ambiguity; no shared-daemon fault injection."""
import io
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import gflo.browser_pair as pair

class PairUncertaintyTests(unittest.TestCase):
    def test_timed_out_create_cannot_be_proven_clean_by_current_absence(self):
        self.create_error=lambda args:subprocess.TimeoutExpired(args,30)
        self.check_uncertainty()

    def test_failed_create_without_returned_id_is_conservatively_uncertain(self):
        self.create_error=lambda args:subprocess.CalledProcessError(1,args)
        self.check_uncertainty()

    def test_malformed_create_reply_retains_uncertainty(self):
        self.create_error=lambda args:None
        self.check_uncertainty()

    def check_uncertainty(self):
        with tempfile.TemporaryDirectory() as root:
            facts=Path(root)/'facts.json'
            spec={'app_name':'owned-app','browser_name':'owned-browser','app_image':'a','browser_image':'b','run':'owned-run','facts':str(facts),'app_args':['docker','run','--rm','--name','owned-app'],'browser_args':[]}
            def docker(args,**kwargs):
                if args[1]=='create':
                    error=self.create_error(args)
                    if error:raise error
                    return SimpleNamespace(stdout=b'incomplete-id')
                if args[1]=='rm':return SimpleNamespace(returncode=1,stderr=b'No such container')
                if args[1]=='ps':return SimpleNamespace(stdout=b'')
                self.fail(args)
            stdin=SimpleNamespace(buffer=io.BytesIO(json.dumps(spec).encode()+b'\n'))
            with patch.object(pair.sys,'stdin',stdin),patch.object(pair.select,'select',return_value=([],[],[])),patch.object(pair.subprocess,'run',docker):
                code=pair.main()
            self.assertEqual(code,125)
            self.assertFalse(json.loads(facts.read_bytes())['cleanup']['confirmed'])
