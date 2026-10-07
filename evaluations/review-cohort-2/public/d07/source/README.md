# Webhook authentication utility

Existing action body_bytes is exposed through api.dispatch and python cli.py, accepting one JSON object on stdin and writing one JSON result.

Add action verify with secret:string, body:string, timestamp:nonnegative integer <=2**40, now:nonnegative integer <=2**40, tolerance:integer 0..3600, signature:string. Strings secret/body are <=4000 Unicode code points. Compute HMAC-SHA256 using UTF-8 secret over UTF-8 bytes of decimal timestamp + "." + body. Return a JSON boolean true only when signature is exactly "sha256=" followed by 64 lowercase hex characters equal to that digest AND abs(now-timestamp)<=tolerance. Otherwise return false. Signature is untrusted and may contain any Unicode characters, including empty input. No exceptions for malformed signature. Use a timing-safe digest comparison for well-formed signatures. Never log or return secrets or body.

Example (SQLite requires the documented database to already exist):

```sh
printf '%s\n' '{"action": "verify", "secret": "key", "body": "{}", "timestamp": 100, "now": 105, "tolerance": 5, "signature": "sha256=b6ae95232f7a6f10ed56c0c2931bda6344efb9e66d09bf79943ca1df746bbddf"}' | python cli.py
```

Run tests with python -m unittest discover. Inputs remain unchanged and failures follow the documented CLI error contract.
