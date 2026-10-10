import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

from gflo.environment import EnvironmentStore


def archive(content=b'original'):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode='w', format=tarfile.USTAR_FORMAT) as tar:
        member = tarfile.TarInfo('package/value.txt')
        member.size = len(content)
        tar.addfile(member, io.BytesIO(content))
    return io.BytesIO(stream.getvalue())


class EnvironmentStoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.store = EnvironmentStore(Path(self.temporary.name) / 'environments')
        self.metadata = {'profile': 'python-stdlib', 'image': 'sha256:' + 'a' * 64,
                         'platform': 'linux/amd64', 'recipe_sha256': 'b' * 64,
                         'locks': {}, 'runtime': {'python': '3.12.13'}}

    def publish(self, **kwargs):
        return self.store.publish(archive(), self.metadata,
                                  lambda path: {'passed': True, 'output': 'smoke passed'}, **kwargs)

    def test_published_environment_binds_tree_receipt_and_runtime(self):
        environment = self.publish()
        resolved = self.store.resolve(environment.id, environment.receipt_hash)
        self.assertEqual(resolved.image, self.metadata['image'])
        self.assertEqual(resolved.profile, 'python-stdlib')
        self.assertEqual((resolved.dependencies / 'package/value.txt').read_bytes(), b'original')
        self.assertEqual(resolved.runtime, {'python': '3.12.13'})
        self.assertEqual(self.publish().id, environment.id)
        receipt = json.loads((self.store.root / environment.id / 'receipt.json').read_text())
        self.assertTrue(receipt['checks']['passed'])
        with self.assertRaises(ValueError):
            self.store.resolve('../' + environment.id)

    def test_byte_mode_and_receipt_tampering_invalidate_resolution(self):
        for change in ('bytes', 'mode', 'receipt', 'link'):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory:
                store = EnvironmentStore(Path(directory) / 'store')
                env = store.publish(archive(), self.metadata, lambda path: {'passed': True})
                file = env.dependencies / 'package/value.txt'
                if change == 'bytes':
                    file.chmod(0o644); file.write_bytes(b'changed'); file.chmod(0o444)
                elif change == 'mode':
                    file.chmod(0o555)
                elif change == 'receipt':
                    path = store.root / env.id / 'receipt.json'
                    path.chmod(0o644); path.write_text('{}'); path.chmod(0o444)
                else:
                    file.parent.chmod(0o755); file.unlink(); file.symlink_to('/etc/passwd')
                with self.assertRaises(ValueError):
                    store.resolve(env.id, env.receipt_hash)
                store.remove_private_staging()  # Does not delete published artifacts.
                self.assertTrue((store.root / env.id).exists())
                # Permit the test fixture owner to dispose of its private store.
                for path in sorted(store.root.rglob('*')):
                    if path.is_dir() and not path.is_symlink(): path.chmod(0o700)

    def test_failed_or_cancelled_checks_cannot_replace_a_good_receipt(self):
        good = self.publish()
        original = (self.store.root / good.id / 'receipt.json').read_bytes()
        with self.assertRaisesRegex(ValueError, 'smoke'):
            self.store.publish(archive(b'bad'), self.metadata, lambda path: {'passed': False})
        cancelled = [False]
        def check(path):
            cancelled[0] = True
            return {'passed': True}
        with self.assertRaisesRegex(ValueError, 'cancelled'):
            self.store.publish(archive(b'cancelled'), self.metadata, check,
                               cancelled=lambda: cancelled[0])
        self.assertEqual((self.store.root / good.id / 'receipt.json').read_bytes(), original)
        self.assertEqual([p.name for p in self.store.root.iterdir() if len(p.name) == 64], [good.id])
        self.assertFalse(list(self.store.root.glob('.prepare-*')))

    def test_post_rename_failure_retires_new_publication(self):
        import os
        import stat
        from unittest.mock import patch
        good = self.publish()
        original_fsync = os.fsync
        def fail_directory(descriptor):
            if stat.S_ISDIR(os.fstat(descriptor).st_mode):
                raise OSError('injected publication durability failure')
            return original_fsync(descriptor)
        with patch('gflo.environment.os.fsync', side_effect=fail_directory):
            with self.assertRaisesRegex(OSError, 'durability'):
                self.store.publish(archive(b'new'), self.metadata, lambda path: {'passed': True})
        self.assertEqual([p.name for p in self.store.root.iterdir() if len(p.name) == 64], [good.id])
        self.assertEqual(self.store.resolve(good.id).id, good.id)

    def test_resolver_cannot_observe_an_in_progress_publication(self):
        good = self.publish()
        def check(path):
            with self.assertRaisesRegex(ValueError, 'preparation'):
                self.store.resolve(good.id, wait=0)
            return {'passed': True}
        self.store.publish(archive(b'next'), self.metadata, check)

    def test_failed_retirement_leaves_a_non_runnable_pending_candidate(self):
        import os
        import stat
        from unittest.mock import patch
        good = self.publish()
        original_fsync, original_rename = os.fsync, Path.rename
        def fail_publication(descriptor):
            if stat.S_ISDIR(os.fstat(descriptor).st_mode) and os.readlink(f'/proc/self/fd/{descriptor}') == str(self.store.root):
                raise OSError('injected publication failure')
            return original_fsync(descriptor)
        def fail_retirement(path, target):
            if len(path.name) == 64:
                raise OSError('injected retirement failure')
            return original_rename(path, target)
        with patch('gflo.environment.os.fsync', side_effect=fail_publication), patch.object(Path, 'rename', fail_retirement):
            with self.assertRaisesRegex(OSError, 'retirement'):
                self.store.publish(archive(b'pending'), self.metadata, lambda path: {'passed': True})
        failed = [p for p in self.store.root.iterdir() if len(p.name) == 64 and p.name != good.id]
        self.assertEqual(len(failed), 1)
        with self.assertRaisesRegex(ValueError, 'pending'):
            self.store.resolve(failed[0].name)
        self.assertEqual(self.store.resolve(good.id).id, good.id)

    def test_cancellation_before_final_commit_keeps_candidate_unpublished(self):
        import os
        import stat
        from unittest.mock import patch
        good = self.publish()
        original_fsync, cancelled = os.fsync, [False]
        def cancel_after_sync(descriptor):
            original_fsync(descriptor)
            if stat.S_ISDIR(os.fstat(descriptor).st_mode) and os.readlink(f'/proc/self/fd/{descriptor}') == str(self.store.root):
                cancelled[0] = True
        with patch('gflo.environment.os.fsync', side_effect=cancel_after_sync):
            with self.assertRaisesRegex(ValueError, 'cancelled'):
                self.store.publish(archive(b'late cancellation'), self.metadata,
                                   lambda path: {'passed': True}, cancelled=lambda: cancelled[0])
        self.assertEqual([p.name for p in self.store.root.iterdir() if len(p.name) == 64], [good.id])
