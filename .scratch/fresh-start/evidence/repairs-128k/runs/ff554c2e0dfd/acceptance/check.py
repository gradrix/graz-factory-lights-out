import concurrent.futures
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


class InventoryAcceptance(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = str(Path(self.temp.name) / 'inventory.sqlite')

    def command(self, *args):
        return subprocess.run(['python', 'cli.py', self.db, *args], capture_output=True, text=True)

    def test_atomic_reservations_and_existing_commands(self):
        put = self.command('put', 'BOOK', '5')
        self.assertEqual(put.returncode, 0, put.stderr)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: self.command('reserve', 'BOOK', '4'), range(2)))
        for result in results:
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(sorted(json.loads(r.stdout)['reserved'] for r in results), [False, True])
        self.assertEqual(json.loads(self.command('get', 'BOOK').stdout), {'sku': 'BOOK', 'quantity': 1})
        missing = self.command('reserve', 'MISSING', '1')
        self.assertEqual(json.loads(missing.stdout), {'sku': 'MISSING', 'reserved': False, 'quantity': None})

    def test_invalid_quantities(self):
        self.command('put', 'BOOK', '5')
        for quantity in ('0', '-1', '1.5', 'invalid'):
            result = self.command('reserve', 'BOOK', quantity)
            self.assertEqual(result.returncode, 2, result)
            self.assertNotIn('Traceback', result.stderr)
        self.assertEqual(json.loads(self.command('get', 'BOOK').stdout)['quantity'], 5)


unittest.main()
