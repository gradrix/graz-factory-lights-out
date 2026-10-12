import io
import json
from pathlib import Path
import tempfile
import unittest

from gflo.artifacts import ArchiveLimits, unpack_archive


CORPUS = Path(__file__).resolve().parents[1] / 'evaluations/environment-artifacts'


class ArchiveTests(unittest.TestCase):
    def test_independent_archives_validate_before_any_extraction(self):
        manifest = json.loads((CORPUS / 'manifest.json').read_text())
        with tempfile.TemporaryDirectory() as directory:
            for case in manifest['archive_cases']:
                with self.subTest(case=case['id']):
                    destination = Path(directory) / case['id']
                    stream = io.BytesIO((CORPUS / case['archive']).read_bytes())
                    if case['expected_result'] == 'accept':
                        unpack_archive(stream, destination, ArchiveLimits(**case['bounds']))
                        self.assertTrue(destination.is_dir())
                        self.assertFalse(any(p.is_symlink() for p in destination.rglob('*')))
                    else:
                        with self.assertRaises(ValueError):
                            unpack_archive(stream, destination, ArchiveLimits(**case['bounds']))
                        self.assertFalse(destination.exists())

    def test_declared_expansion_is_rejected_without_waiting_for_body(self):
        manifest = json.loads((CORPUS / 'manifest.json').read_text())
        case = next(case for case in manifest['archive_cases'] if 'declared' in case['id'])
        header = (CORPUS / case['archive']).read_bytes()[:512]
        class HeaderOnly:
            calls = 0
            def read(self, size):
                self.calls += 1
                if self.calls > 1:
                    raise AssertionError('Requested an attacker-declared body')
                return header
        stream = HeaderOnly()
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, 'expanded-byte'):
                unpack_archive(stream, Path(directory) / 'snapshot', ArchiveLimits(**case['bounds']))
            self.assertEqual(stream.calls, 1)

    def test_existing_destination_link_is_not_followed_or_removed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root / 'outside'
            outside.mkdir()
            (outside / 'keep').write_text('original')
            destination = root / 'snapshot'
            destination.symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'destination'):
                unpack_archive(io.BytesIO(bytes(1024)), destination)
            self.assertTrue(destination.is_symlink())
            self.assertEqual((outside / 'keep').read_text(), 'original')

    def test_valid_content_and_execution_mode_are_preserved(self):
        import tarfile
        data = io.BytesIO()
        with tarfile.open(fileobj=data, mode='w', format=tarfile.USTAR_FORMAT) as archive:
            info = tarfile.TarInfo('bin/check')
            info.size, info.mode = 4, 0o755
            archive.addfile(info, io.BytesIO(b'pass'))
        with tempfile.TemporaryDirectory() as directory:
            result = unpack_archive(io.BytesIO(data.getvalue()), Path(directory) / 'snapshot')
            self.assertEqual((result / 'bin/check').read_bytes(), b'pass')
            self.assertEqual((result / 'bin/check').stat().st_mode & 0o777, 0o555)
