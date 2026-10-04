import unittest
from fastapi.testclient import TestClient
from config_preview.app import app
from config_preview.domain import preview
from config_preview.errors import Conflict
class ConfigTests(unittest.TestCase):
    def test_http_set(self):
        r=TestClient(app).post('/config/preview',json={'base':{},'operations':[{'op':'set','path':['x'],'value':3}]})
        self.assertEqual(r.status_code,200);self.assertEqual(r.json()['document'],{'x':3})
    def test_atomic_conflict(self):
        base={'a':False}
        with self.assertRaises(Conflict):preview(base,[{'op':'set','path':['b'],'value':2},{'op':'test','path':['a'],'value':0}])
        self.assertEqual(base,{'a':False})
    def test_absent_null(self):
        result=preview({},[{'op':'set','path':['x'],'value':None}])
        self.assertEqual(result['audit'][0]['before'],{'present':False,'value':None})
        self.assertEqual(result['audit'][0]['after'],{'present':True,'value':None})
