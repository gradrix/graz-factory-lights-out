# Configuration preview

This installable package previews ordered nested configuration changes without modifying the request. Set, remove and test operate on explicit key lists. A conflict aborts the preview atomically; missing keys and failed typed tests produce indexed HTTP409 errors. Invalid shapes use HTTP422. Null differs from an absent key; booleans differ from integers.

After offline wheel installation, run `python -m uvicorn config_preview.app:app --host 127.0.0.1 --port 8000`. Send POST `/config/preview` with `{"base":{},"operations":[]}`; response is `{"document":{},"audit":[]}`. GET `/health` remains available. Run tests with `python -m unittest discover -s /path/to/project` using the installed package and approved dependencies.
