import unittest
import requests as r

class TestClass(unittest.TestCase):
    def test_hello_world_app(self):
        response = r.get('http://127.0.0.1:8000/').json()
        excepted = {"message": "Hello World"}
        self.assertEqual(excepted, response)


