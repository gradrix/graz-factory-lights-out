from pathlib import Path
assert Path('/workspace/app.py').read_text() == 'value=2\n'
