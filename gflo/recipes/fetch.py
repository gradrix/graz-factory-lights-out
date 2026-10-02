"""Trusted fixed-artifact HTTPS client. No fetched code is executed here."""
import hashlib
import http.client
import io
import ipaddress
import json
from pathlib import Path
import re
import socket
import ssl
import sys
import tarfile
import urllib.parse

HOSTS = {'files.pythonhosted.org', 'registry.npmjs.org'}


def validate(spec):
    url = spec['url']
    if not isinstance(url, str) or any(ord(c) <= 32 or ord(c) >= 127 for c in url) or '\\' in url:
        raise ValueError('noncanonical URL')
    parsed = urllib.parse.urlsplit(url)
    if (parsed.scheme != 'https' or parsed.hostname not in HOSTS or
            parsed.netloc not in (parsed.hostname, parsed.hostname + ':443') or
            parsed.port not in (None, 443) or parsed.username or parsed.password or
            parsed.fragment or parsed.query or not parsed.path.startswith('/')):
        raise ValueError('URL denied')
    algorithm = spec['algorithm']
    if algorithm not in ('sha256', 'sha512') or not re.fullmatch(
            '[0-9a-f]{' + ('64' if algorithm == 'sha256' else '128') + '}', spec['digest']):
        raise ValueError('invalid artifact hash')
    if type(spec['max_bytes']) is not int or not 0 < spec['max_bytes'] <= 16 * 1024 * 1024:
        raise ValueError('invalid artifact cap')
    if not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_.+-]{0,199}', spec['filename']):
        raise ValueError('invalid artifact filename')
    return parsed


def resolve(host):
    records = socket.getaddrinfo(host, 443, socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
    addresses = sorted({record[4][0] for record in records})
    if not addresses:
        raise ValueError('empty DNS answer')
    for item in addresses:
        address = ipaddress.IPv4Address(item)
        if not address.is_global or address.is_multicast or address.is_reserved:
            raise ValueError('nonpublic DNS answer')
    return addresses


class Connection(http.client.HTTPSConnection):
    def __init__(self, host, address):
        context = ssl.create_default_context()
        context.set_alpn_protocols(['http/1.1'])
        super().__init__(host, 443, timeout=10, context=context)
        self.address = address

    def connect(self):
        raw = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        raw.settimeout(self.timeout)
        try:
            raw.connect((self.address, 443))
            self.sock = self._context.wrap_socket(raw, server_hostname=self.host)
        except BaseException:
            raw.close()
            raise


def consume(response, spec):
    if response.status != 200:
        raise ValueError('non-200 response; redirects forbidden')
    if response.getheader('Content-Encoding') not in (None, 'identity'):
        raise ValueError('encoded body forbidden')
    length = response.getheader('Content-Length')
    if length is not None and (not length.isdecimal() or int(length) > spec['max_bytes']):
        raise ValueError('declared byte cap')
    data = bytearray()
    while True:
        block = response.read(min(65536, spec['max_bytes'] - len(data) + 1))
        if not block:
            break
        data.extend(block)
        if len(data) > spec['max_bytes']:
            raise ValueError('actual byte cap')
    if length is not None and len(data) != int(length):
        raise ValueError('incomplete length')
    if hashlib.new(spec['algorithm'], data).hexdigest() != spec['digest']:
        raise ValueError('lock hash mismatch')
    return data


def fetch(spec):
    parsed = validate(spec)
    addresses = resolve(parsed.hostname)
    connection = Connection(parsed.hostname, addresses[0])
    try:
        connection.request('GET', parsed.path, headers={'Host': parsed.hostname,
                           'Accept-Encoding': 'identity', 'Connection': 'close'})
        data = consume(connection.getresponse(), spec)
        print(json.dumps({'host': parsed.hostname, 'connected': addresses[0],
                          'filename': spec['filename'], 'bytes': len(data),
                          'algorithm': spec['algorithm'], 'digest': spec['digest']}), file=sys.stderr)
        return data
    finally:
        connection.close()


def main():
    specs = json.loads(Path('/approved/artifacts.json').read_text())
    if not isinstance(specs, list) or not 1 <= len(specs) <= 32:
        raise ValueError('artifact count limit')
    names = set()
    for spec in specs:
        validate(spec)
        if spec['filename'] in names:
            raise ValueError('duplicate artifact filename')
        names.add(spec['filename'])
    total = 0
    with tarfile.open(fileobj=sys.stdout.buffer, mode='w|', format=tarfile.USTAR_FORMAT) as archive:
        for spec in specs:
            data = fetch(spec)
            total += len(data)
            if total > 64 * 1024 * 1024:
                raise ValueError('aggregate artifact cap')
            header = tarfile.TarInfo(spec['filename'])
            header.size, header.mode = len(data), 0o444
            archive.addfile(header, io.BytesIO(data))


if __name__ == '__main__':
    main()
