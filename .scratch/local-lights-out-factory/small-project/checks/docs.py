"""Check declared documentation topics; this does not judge prose quality."""

from pathlib import Path

text = Path("README.md").read_text().lower()
for word in ("install", "--file", "add", "list", "done", "export", "pytest", "json", "single"):
    assert word in text, word
assert "/home/" not in text and "/users/" not in text
print("docs-ok")
