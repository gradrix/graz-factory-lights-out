"""Fixed public-document client. Separate policy from locked package fetching."""
import hashlib
import json
from pathlib import Path
import re
import sys
import urllib.parse

try:
    from .fetch import Connection, resolve
except ImportError:  # Standalone fixed helper in the acquisition executor.
    from fetch import Connection, resolve

BODY_LIMIT = 2 * 1024 * 1024
HEADER_LIMIT = 8192


def decode(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate JSON field')
            result[key] = value
        return result
    def invalid(value):
        raise ValueError('Nonfinite JSON value')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)


def approval(value):
    if not isinstance(value, dict) or set(value) not in (
            {'url', 'source_version', 'question'}, {'url', 'source_version', 'question', 'expected_sha256'}):
        raise ValueError('Approval requires exact URL, source_version and question')
    for key, limit in [('url', 2048), ('source_version', 256), ('question', 2048)]:
        if not isinstance(value[key], str) or not value[key].strip() or len(value[key].encode()) > limit:
            raise ValueError('Invalid approved ' + key)
    url = value['url']
    if any(ord(c) <= 32 or ord(c) >= 127 for c in url) or '\\' in url or '?' in url or '#' in url:
        raise ValueError('Noncanonical approved URL')
    parsed = urllib.parse.urlsplit(url)
    if (parsed.scheme != 'https' or not parsed.hostname or
            parsed.netloc not in (parsed.hostname, parsed.hostname + ':443') or
            parsed.port not in (None, 443) or parsed.username or parsed.password or
            not parsed.path.startswith('/') or re.search(r'%(?:0[0-9a-f]|1[0-9a-f]|7f|5c)', url, re.I)):
        raise ValueError('Approved URL must be exact public HTTPS without URL options')
    if 'expected_sha256' in value and (not isinstance(value['expected_sha256'], str) or
                                      not re.fullmatch('[0-9a-f]{64}', value['expected_sha256'])):
        raise ValueError('Invalid expected SHA256')
    return parsed


def policy(headers):
    """Reject ambiguous transport/retention before reading response bytes."""
    if len(headers) > 64 or sum(len(k.encode()) + len(v.encode()) for k, v in headers) > HEADER_LIMIT:
        raise ValueError('HTTP header bounds')
    normalized = {}
    for key, value in headers:
        key = key.lower()
        if any(ord(c) < 32 and c != '\t' or ord(c) == 127 for c in value):
            raise ValueError('Malformed HTTP header')
        if key in normalized:
            raise ValueError('Duplicate HTTP header')
        normalized[key] = value.strip()
    if 'set-cookie' in normalized or 'content-disposition' in normalized:
        raise ValueError('Personalized or attachment response cannot be retained')
    if normalized.get('content-encoding', 'identity').lower() != 'identity' or 'transfer-encoding' in normalized:
        raise ValueError('Unsupported transport encoding')
    kind = re.fullmatch(r'(text/(?:plain|html))(?:\s*;\s*charset\s*=\s*"?(utf-8)"?)?',
                        normalized.get('content-type', '').lower())
    if not kind:
        raise ValueError('Only UTF-8 HTML/plain documents supported')
    cache = normalized.get('cache-control', '')
    seen = set()
    for part in cache.split(',') if cache else []:
        name, separator, val = part.strip().lower().partition('=')
        if name in seen:
            raise ValueError('Ambiguous cache policy')
        seen.add(name)
        if name in ('public', 'immutable') and not separator:
            continue
        if name in ('max-age', 's-maxage', 'stale-while-revalidate', 'stale-if-error') and separator and re.fullmatch('[0-9]{1,10}', val):
            continue
        raise ValueError('Unsupported offline retention policy: ' + name)
    if 'pragma' in normalized or 'vary' in normalized and normalized['vary'].lower() not in ('accept-encoding',):
        raise ValueError('Unsupported offline retention variation')
    length = normalized.get('content-length')
    if length is None or not re.fullmatch('[0-9]{1,10}', length) or int(length) > BODY_LIMIT:
        raise ValueError('Bounded unambiguous Content-Length required')
    return {'content_type': kind[1], 'charset': 'utf-8', 'cache_control': cache,
            'body_size': int(length), 'http_headers': normalized}


def frame(metadata, body):
    header = json.dumps(metadata, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()
    if len(header) > HEADER_LIMIT or len(body) > BODY_LIMIT:
        raise ValueError('Document frame exceeds bounds')
    return header + b'\n' + body


def unpack(data, approved):
    approval(approved)
    header, separator, body = data.partition(b'\n')
    if not separator or len(header) > HEADER_LIMIT or len(body) > BODY_LIMIT:
        raise ValueError('Invalid document frame bounds')
    metadata = decode(header)
    if (metadata.get('url') != approved['url'] or metadata.get('status') != 200 or
            type(metadata.get('body_size')) is not int or metadata['body_size'] != len(body)):
        raise ValueError('Document frame identity/length mismatch')
    # Recheck HTTP facts at the controller, not only in the online helper.
    checked = policy(list(metadata['http_headers'].items()))
    if any(metadata.get(k) != v for k, v in checked.items()):
        raise ValueError('Document frame HTTP facts disagree')
    import ipaddress
    address = ipaddress.IPv4Address(metadata['connected'])
    if not address.is_global or address.is_multicast or address.is_reserved:
        raise ValueError('Nonpublic connection evidence')
    if 'expected_sha256' in approved and hashlib.sha256(body).hexdigest() != approved['expected_sha256']:
        raise ValueError('Expected document hash mismatch')
    return metadata, body


def fetch(approved):
    parsed = approval(approved)
    addresses = resolve(parsed.hostname)  # One resolution, no reconnect/fallback.
    connection = Connection(parsed.hostname, addresses[0])
    try:
        connection.request('GET', parsed.path, headers={'Host': parsed.hostname,
                           'Accept-Encoding': 'identity', 'Connection': 'close'})
        response = connection.getresponse()
        if response.status != 200:
            raise ValueError('Non-200 document response; redirects forbidden')
        metadata = policy(response.getheaders())
        body = response.fp.read(metadata['body_size'] + 1)  # Require EOF, including bytes beyond Content-Length.
        if len(body) != metadata['body_size']:
            raise ValueError('Incomplete or oversized document body')
        metadata.update(url=approved['url'], status=200, connected=addresses[0])
        result = frame(metadata, body)
        unpack(result, approved)
        return result
    finally:
        connection.close()


if __name__ == '__main__':
    try:
        sys.stdout.buffer.write(fetch(decode(Path('/approved').read_bytes())))
    except Exception as error:
        print(str(error)[:2048], file=sys.stderr)
        raise SystemExit(1)
