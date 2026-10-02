import io
import json
import unittest
from unittest.mock import patch
from gflo.recipes import document, document_extract

APP={'url':'https://docs.python.org/3.12/library/json.html','source_version':'Python 3.12 docs','question':'What is JSON?'}

class DocumentProtocolTests(unittest.TestCase):
    def test_parser_instruction_events_are_bounded(self):
        with self.assertRaisesRegex(ValueError,'event'):
            document_extract.extract(b'<?instruction ?>'*10001+b'<p>visible</p>','text/html')

    def test_ambiguous_duplicate_json_fields_are_rejected(self):
        with self.assertRaises(ValueError):
            document.decode('{"url":"one","url":"two"}')

    def test_approval_rejects_url_options_and_unbounded_authority(self):
        for url in ['http://docs.python.org/x', 'https://docs.python.org/x?',
                    'https://docs.python.org/x#', 'https://user@docs.python.org/x',
                    'https://docs.python.org:444/x', 'https://docs.python.org/x%0a',
                    'https://docs.python.org/x\\y', 'https://docs.python.org/é']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                document.approval(dict(APP,url=url))
        for change in [{'question':''}, {'source_version':'x'*257}, {'expected_sha256':'A'*64}]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                document.approval(dict(APP,**change))
        with self.assertRaises(ValueError):
            document.approval(dict(APP,extra=True))
        self.assertEqual(document.approval(APP).hostname,'docs.python.org')

    def test_retention_and_transport_fail_closed(self):
        base=[('Content-Type','text/html; charset=utf-8'),('Content-Length','12')]
        for header in [('Cache-Control',v) for v in ['private','no-store','no-cache','must-revalidate','proxy-revalidate','public, public','unknown=1','max-age=oops']] + [
            ('Set-Cookie','id=1'),('Content-Disposition','attachment'),('Content-Encoding','gzip'),
            ('Transfer-Encoding','chunked'),('Pragma','no-cache'),('Vary','Cookie'),('X-Bad','a\nb')]:
            with self.subTest(header=header), self.assertRaises(ValueError):
                document.policy(base+[header])
        for headers in [base+base,base+[('x','a'*8192)],base+[('x'+str(i),'v') for i in range(64)],
                        [('Content-Type','application/pdf'),('Content-Length','12')],
                        [('Content-Type','text/plain')], [('Content-Type','text/plain'),('Content-Length',str(document.BODY_LIMIT+1))]]:
            with self.subTest(headers=headers[:2]), self.assertRaises(ValueError):
                document.policy(headers)
        facts=document.policy(base+[('Cache-Control','public, max-age=3600, immutable'),('Vary','Accept-Encoding')])
        self.assertEqual(facts['body_size'],12)

    def test_fetch_requires_exact_body_and_never_follows_redirect(self):
        from unittest.mock import Mock
        for status,body,expected in [(200,b'hello',True),(200,b'hell',False),(200,b'hellox',False),(302,b'hello',False)]:
            connection=Mock();response=connection.getresponse.return_value
            response.status=status;response.fp=io.BytesIO(body)
            response.getheaders.return_value=[('Content-Type','text/plain'),('Content-Length','5')]
            with self.subTest(status=status,body=body), patch.object(document,'resolve',return_value=['1.1.1.1']) as dns, patch.object(document,'Connection',return_value=connection):
                if expected:
                    framed=document.fetch(APP)
                    self.assertEqual(document.unpack(framed,APP)[1],b'hello')
                    with self.assertRaises(ValueError):
                        document.unpack(framed,dict(APP,expected_sha256='0'*64))
                else:
                    with self.assertRaises(ValueError): document.fetch(APP)
                dns.assert_called_once();connection.close.assert_called_once()
                if status==302: self.assertEqual(response.fp.tell(),0)

    def test_extraction_preserves_order_without_active_content(self):
        body=b'<!doctype html><html><head><title>hidden</title></head><body><!--hidden--><h1>Title</h1><p>A &amp; B<br/>next</p><script>hidden</script><template><p>hidden</p></template><p>Last <b>word</b></p></body></html>'
        self.assertEqual(document_extract.extract(body,'text/html'),['Title','A & B','next','Last word'])
        self.assertEqual(document_extract.extract(b' a  b\n\n c ','text/plain'),['a b','c'])

    def test_extraction_rejects_incomplete_or_oversized_evidence(self):
        cases=[(b'\xff','text/plain'),(b'a\x00b','text/plain'),(b'','text/plain'),(b'x','application/pdf'),
               (b'x'*(document_extract.TEXT_LIMIT+1),'text/plain'),
               (b'<p>'+b'x'*(document_extract.TEXT_LIMIT+1)+b'</p>','text/html'),
               (b'<div>'*65+b'x','text/html'),(b'<p>x</p>'*2049,'text/html'),
               (b'x\n'*2049,'text/plain')]
        for body,kind in cases:
            with self.subTest(kind=kind,size=len(body)), self.assertRaises(ValueError):
                document_extract.extract(body,kind)
        with self.assertRaises(ValueError): document.decode('NaN')

    def test_frames_reject_identity_size_policy_and_connection_mismatch(self):
        metadata=dict(document.policy([('Content-Type','text/plain'),('Content-Length','1')]),url=APP['url'],status=200,connected='1.1.1.1')
        for change in [{'url':'https://other.invalid/x'},{'status':302},{'body_size':True},{'body_size':2},{'content_type':'text/html'},{'connected':'127.0.0.1'}]:
            with self.subTest(change=change),self.assertRaises(ValueError):
                document.unpack(document.frame(dict(metadata,**change),b'x'),APP)
        for raw in [b'no newline', b'x'*8193+b'\nx', document.frame(metadata,b'')]:
            with self.assertRaises(ValueError):document.unpack(raw,APP)
        for meta,body in [({'x':'x'*8192},b''),({},b'x'*(document.BODY_LIMIT+1))]:
            with self.assertRaises(ValueError):document.frame(meta,body)
