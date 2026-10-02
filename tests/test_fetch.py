import hashlib
import io
import unittest
from unittest.mock import patch
from gflo.recipes.fetch import validate, consume, resolve


class FetchTests(unittest.TestCase):
    def spec(self):
        return {'filename': 'package.whl', 'url': 'https://files.pythonhosted.org/packages/example.whl',
                'algorithm': 'sha256', 'digest': hashlib.sha256(b'good').hexdigest(), 'max_bytes': 4}

    def test_only_exact_public_registry_urls_and_safe_output_names(self):
        self.assertEqual(validate(self.spec()).hostname, 'files.pythonhosted.org')
        for url in ['http://files.pythonhosted.org/x', 'https://localhost/x',
                    'https://files.pythonhosted.org.evil/x', 'https://files.pythonhosted.org/x?token=y',
                    'https://user@files.pythonhosted.org/x', 'https://files.pythonhosted.org:444/x']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate(dict(self.spec(), url=url))
        for name in ['../x', '/x', 'a/b', '.', '']:
            with self.subTest(name=name), self.assertRaises(ValueError):
                validate(dict(self.spec(), filename=name))

    def test_body_caps_hashes_status_encoding_and_incomplete_length(self):
        class Response(io.BytesIO):
            status = 200
            headers = {}
            def getheader(self, name): return self.headers.get(name)
        self.assertEqual(consume(Response(b'good'), self.spec()), b'good')
        for body, status, headers in [(b'evil', 200, {}), (b'good!', 200, {}),
                (b'good', 302, {}), (b'good', 200, {'Content-Encoding':'gzip'}),
                (b'goo', 200, {'Content-Length':'4'}), (b'', 200, {'Content-Length':'9999'})]:
            response=Response(body);response.status=status;response.headers=headers
            with self.subTest(body=body,status=status,headers=headers), self.assertRaises(ValueError):
                consume(response, self.spec())

    def test_any_private_dns_answer_rejects_entire_set(self):
        with patch('socket.getaddrinfo', return_value=[(2,1,6,'',('1.1.1.1',443)), (2,1,6,'',('127.0.0.1',443))]):
            with self.assertRaisesRegex(ValueError, 'nonpublic'):
                resolve('files.pythonhosted.org')
