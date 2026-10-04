# Manifest reconciliation

Compare two file manifests without touching files. Entries carry relative paths, integer sizes and lowercase SHA256 values. Shared paths are classified before unique unmatched signatures become renames; ambiguous signatures remain added and removed paths. Invalid data returns an error without changing inputs.

Run `python /path/to/project/main.py` and send `{"action":"compare","before":[],"after":[]}`. The response is `{"added":[],"removed":[],"modified":[],"renamed":[],"unchanged":[],"summary":{"before_bytes":0,"after_bytes":0,"delta_bytes":0}}`.

Run tests with `python -m unittest discover -s /path/to/project`. Malformed JSON exits2 with `{"error":"invalid input"}`; successful JSON exits0.
