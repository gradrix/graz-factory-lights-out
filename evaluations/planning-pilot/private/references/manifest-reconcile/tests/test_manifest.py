import unittest
from manifest_tool.api import run
from manifest_tool.domain import compare
class ManifestTests(unittest.TestCase):
    def test_rename(self):
        a={'path':'old','size':2,'sha256':'a'*64};b=dict(a,path='new')
        self.assertEqual(compare([a],[b])['renamed'],[{'from':'old','to':'new'}])
    def test_ambiguous(self):
        a=lambda p:{'path':p,'size':0,'sha256':'b'*64}
        self.assertEqual(compare([a('x'),a('y')],[a('z')])['renamed'],[])
    def test_bool_rejection(self):
        with self.assertRaises(ValueError):compare([{'path':'x','size':True,'sha256':'a'*64}],[])
