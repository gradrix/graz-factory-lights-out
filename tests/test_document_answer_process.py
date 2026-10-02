import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

from gflo.documents import bounded_answer


class Client:
    def request(self, *args, **kwargs):
        return {'choices': []}


class AnswerProcessTests(unittest.TestCase):
    def test_bounded_child_returns_response(self):
        self.assertEqual(bounded_answer(Client(), {}, lambda: False), {'choices': []})

    def test_owner_death_terminates_child_and_releases_lease(self):
        with tempfile.TemporaryDirectory() as directory:
            script = '''import fcntl, os, pathlib, time
from gflo.documents import bounded_answer
root=pathlib.Path(__import__('sys').argv[1])
lock=open(root/'lock','w');fcntl.flock(lock,fcntl.LOCK_EX)
class Client:
 def request(self,*a,**kw):
  (root/'child').write_text(str(os.getpid()))
  while True: time.sleep(.1)
bounded_answer(Client(),{},lambda:False)
'''
            owner = subprocess.Popen([sys.executable, '-c', script, directory])
            child = None
            try:
                deadline = time.monotonic() + 5
                while not (Path(directory)/'child').exists() and time.monotonic()<deadline:
                    time.sleep(.02)
                child=int((Path(directory)/'child').read_text())
                owner.kill();owner.wait(timeout=5)
                import fcntl
                with open(Path(directory)/'lock','a') as lock:
                    while True:
                        try:
                            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                            break
                        except BlockingIOError:
                            if time.monotonic()>deadline:
                                self.fail('Orphan answer child retained store lease after owner death')
                            time.sleep(.02)
            finally:
                if owner.poll() is None: owner.kill();owner.wait()
                if child:
                    try: os.kill(child,signal.SIGKILL)
                    except ProcessLookupError: pass

    def test_child_errors_oversize_and_cancellation_are_bounded(self):
        class ErrorClient:
            def request(self,*a,**kw):raise RuntimeError('offline endpoint')
        class LargeClient:
            def request(self,*a,**kw):return {'text':'x'*65536}
        class SlowClient:
            def request(self,*a,**kw):time.sleep(10)
        for client in [ErrorClient(),LargeClient()]:
            with self.subTest(client=type(client).__name__),self.assertRaises(ValueError):
                bounded_answer(client,{},lambda:False)
        started=time.monotonic()
        with self.assertRaises(ValueError):bounded_answer(SlowClient(),{},lambda:True)
        self.assertLess(time.monotonic()-started,2)
