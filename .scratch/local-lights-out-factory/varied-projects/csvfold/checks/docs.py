from pathlib import Path
text = Path('README.md').read_text().lower()
for word in ('install', 'cli', 'core.run', 'pytest', 'input', 'order', 'invalid'):
    assert word in text, ('missing documentation', word)
assert len(text) >= 250, 'README too small'
print('docs-ok')
