"""Offline deterministic source-text extraction; no rendering or asset loading."""
from html.parser import HTMLParser
import json
from pathlib import Path
import sys

TEXT_LIMIT = 128 * 1024
EVENT_LIMIT = 10000
DEPTH_LIMIT = 64
BLOCK_LIMIT = 2048
VERSION = 'document-text-v1'
DROP = {'script', 'style', 'template', 'head', 'noscript', 'iframe', 'object', 'svg', 'canvas'}
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}
BLOCK = {'p', 'div', 'section', 'article', 'li', 'dt', 'dd', 'tr', 'pre', 'blockquote', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'br', 'hr'}


class Extractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.spans, self.parts = [], [], []
        self.events = self.bytes = 0

    def event(self):
        self.events += 1
        if self.events > EVENT_LIMIT:
            raise ValueError('HTML event limit')

    def flush(self):
        text = ' '.join(''.join(self.parts).split())
        self.parts.clear()
        if text:
            self.spans.append(text)
            if len(self.spans) > BLOCK_LIMIT:
                raise ValueError('Text block limit')

    def handle_starttag(self, tag, attrs):
        self.event()
        if tag in BLOCK:
            self.flush()
        if tag not in VOID:
            self.stack.append(tag)
            if len(self.stack) > DEPTH_LIMIT:
                raise ValueError('HTML depth limit')

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        self.event()
        if tag in BLOCK:
            self.flush()
        if tag in self.stack:
            # HTML permits omitted end tags; close through the matching ancestor.
            self.stack = self.stack[:len(self.stack) - 1 - self.stack[::-1].index(tag)]

    def handle_data(self, data):
        self.event()
        if not any(tag in DROP for tag in self.stack):
            self.bytes += len(data.encode())
            if self.bytes > TEXT_LIMIT:
                raise ValueError('Extracted text byte limit')
            self.parts.append(data)

    def handle_comment(self, data):
        self.event()

    def handle_pi(self, data):
        self.event()

    def handle_decl(self, decl):
        self.event()

    def unknown_decl(self, data):
        raise ValueError('Unsupported HTML declaration')


def extract(body, content_type):
    text = body.decode('utf-8', errors='strict')
    if '\x00' in text:
        raise ValueError('NUL in source text')
    if content_type == 'text/plain':
        spans = [' '.join(line.split()) for line in text.splitlines() if line.strip()]
    elif content_type == 'text/html':
        parser = Extractor()
        parser.feed(text); parser.close(); parser.flush()
        spans = parser.spans
    else:
        raise ValueError('Unsupported document type')
    if not spans or len(spans) > BLOCK_LIMIT or sum(len(s.encode()) for s in spans) > TEXT_LIMIT:
        raise ValueError('Empty or oversized extracted text')
    return spans


if __name__ == '__main__':
    try:
        metadata = json.loads(Path('/approved').read_bytes())
        result = extract(Path('/body').read_bytes(), metadata['content_type'])
        sys.stdout.write(json.dumps(result, ensure_ascii=True, separators=(',', ':')))
    except Exception as error:
        print(str(error)[:2048], file=sys.stderr)
        raise SystemExit(1)
