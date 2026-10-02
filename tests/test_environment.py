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
