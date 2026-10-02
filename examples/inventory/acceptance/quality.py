"""Example quality gate: real discovered tests, clean deliverable and usage docs."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, '/workspace')
root = Path('/workspace')
extras = [str(p.relative_to(root)) for p in root.rglob('*')
          if p.is_file() and p.suffix not in ('.py', '.md')]
if extras:
    raise SystemExit('Remove scratch/non-deliverable files: ' + ', '.join(extras))
readme = root / 'README.md'
if not readme.is_file() or len(readme.read_text().strip()) < 80:
    raise SystemExit('Provide a concise README with usable commands')
suite = unittest.defaultTestLoader.discover('/workspace/tests')
count = suite.countTestCases()
if count < 3:
    raise SystemExit(f'Expected at least 3 discoverable regression tests; found {count}. Name unittest methods test_*.')
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
