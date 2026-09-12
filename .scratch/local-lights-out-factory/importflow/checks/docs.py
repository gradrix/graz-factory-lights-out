from pathlib import Path
text=Path('README.md').read_text().lower()
for word in ('install','pytest','curl','--db','--blobs','/imports','/result','idempot','lease','stale','sqlite','wal','handler','retention','limit','3'):
    assert word in text,('missing documentation',word)
assert 'single' in text or 'one host' in text, 'document single-host limit'
assert len(text)>1000,'README lacks operational detail'
print('docs-ok')
