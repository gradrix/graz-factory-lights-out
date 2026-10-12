"""Regression tests for the store API (initialize/put/available/reserve)."""
import os
import tempfile
import threading
import time
import unittest

from store import initialize, put, available, reserve


class TestStore(unittest.TestCase):

    def test_put_get_behavior_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            db = os.path.join(d, 'inv.sqlite')
            initialize(db)
            self.assertIsNone(available(db, 'BOOK'))
            put(db, 'BOOK', 10)
            self.assertEqual(available(db, 'BOOK'), 10)
            put(db, 'BOOK', 2)
            self.assertEqual(available(db, 'BOOK'), 2)

    def test_reserve_subtracts_exactly_once(self):
        with tempfile.TemporaryDirectory() as d:
            db = os.path.join(d, 'inv.sqlite')
            initialize(db)
            put(db, 'BOOK', 10)
            self.assertTrue(reserve(db, 'BOOK', 4))
            self.assertEqual(available(db, 'BOOK'), 6)
            self.assertTrue(reserve(db, 'BOOK', 6))
            self.assertEqual(available(db, 'BOOK'), 0)

    def test_reserve_unknown_sku_leaves_stock_unchanged(self):
        with tempfile.TemporaryDirectory() as d:
            db = os.path.join(d, 'inv.sqlite')
            initialize(db)
            put(db, 'BOOK', 3)
            self.assertFalse(reserve(db, 'GHOST', 1))
            self.assertEqual(available(db, 'GHOST'), None)
            self.assertEqual(available(db, 'BOOK'), 3)

    def test_reserve_insufficient_stock_returns_false(self):
        with tempfile.TemporaryDirectory() as d:
            db = os.path.join(d, 'inv.sqlite')
            initialize(db)
            put(db, 'BOOK', 3)
            self.assertFalse(reserve(db, 'BOOK', 4))
            self.assertEqual(available(db, 'BOOK'), 3)

    def test_reserve_non_positive_or_non_integer_quantity(self):
        with tempfile.TemporaryDirectory() as d:
            db = os.path.join(d, 'inv.sqlite')
            initialize(db)
            put(db, 'BOOK', 5)
            for bad in (0, -1, True, False, 2.5, '4', None):
                self.assertFalse(reserve(db, 'BOOK', bad))
            self.assertEqual(available(db, 'BOOK'), 5)

    def test_reserve_never_oversells_concurrently(self):
        """Two reservations of 4 against stock 5: exactly one succeeds, 1 left."""
        with tempfile.TemporaryDirectory() as d:
            db = os.path.join(d, 'inv.sqlite')
            initialize(db)
            put(db, 'BOOK', 5)
            results = []
            start = time.time() + 1.0

            def attempt():
                while time.time() < start:
                    time.sleep(0.001)
                results.append(reserve(db, 'BOOK', 4))

            threads = [threading.Thread(target=attempt) for _ in range(2)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            self.assertEqual(sum(1 for r in results if r), 1)
            self.assertEqual(available(db, 'BOOK'), 1)

    def test_reserve_guarded_update_is_single_atomic_statement(self):
        """The guarded UPDATE must stay a single statement, unpadded."""
        import inspect
        src = inspect.getsource(reserve)
        self.assertNotIn('_GUARD_PAD', src)
        self.assertNotIn('AND 1', src)
        self.assertNotIn('fetchone', src)
        self.assertIn('cur.rowcount > 0', src)
        # Exactly one UPDATE statement in reserve (atomic check-and-subtract).
        self.assertEqual(src.count('UPDATE stock'), 1)



if __name__ == '__main__':
    unittest.main()
