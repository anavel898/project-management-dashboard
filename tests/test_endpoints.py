import unittest

from fastapi.testclient import TestClient

from src.main import app

from json import loads


class TestEndpoints(unittest.TestCase):
    client = TestClient(app)

    def test_create(self):
        requestBody = {"name": "Project 1",
                        "created_by": "anavel",
                        "description": "toy description 1"}
        response = self.client.post("/projects", json=requestBody)
        self.assertEqual(200, response.status_code)

    def test_get_all(self):
        response = self.client.get("/projects")
        self.assertEqual(200, response.status_code)
        # checking if project details are transferred appropriately
        responseAsDict = loads(response.json())
        self.assertEqual(1, len(responseAsDict))
        self.assertIsInstance(responseAsDict["1"], dict)
        self.assertEqual("Project 1", responseAsDict["1"]["name"])
        self.assertEqual(1, responseAsDict["1"]["id"])
        self.assertEqual("toy description 1",
                         responseAsDict["1"]["description"])
        self.assertEqual("anavel", responseAsDict["1"]["created_by"])
        self.assertIsNotNone(responseAsDict["1"]["created_on"])
        self.assertIsNone(responseAsDict["1"]["logo"])
        self.assertIsNone(responseAsDict["1"]["updated_by"])
        self.assertIsNone(responseAsDict["1"]["updated_on"])
        self.assertIsNone(responseAsDict["1"]["documents"])
        self.assertIsNone(responseAsDict["1"]["contributors"])

    def test_get(self):
        response = self.client.get("/project/1/info")
        self.assertEqual(200, response.status_code)
        # checking if project details are transferred appropriately
        responseAsDict = loads(response.json())
        self.assertEqual(10, len(responseAsDict))
        self.assertEqual("Project 1", responseAsDict["name"])
        self.assertEqual(1, responseAsDict["id"])
        self.assertEqual("toy description 1", responseAsDict["description"])
        self.assertEqual("anavel", responseAsDict["created_by"])
        self.assertIsNotNone(responseAsDict["created_on"])
        self.assertIsNone(responseAsDict["logo"])
        self.assertIsNone(responseAsDict["updated_by"])
        self.assertIsNone(responseAsDict["updated_on"])
        self.assertIsNone(responseAsDict["documents"])
        self.assertIsNone(responseAsDict["contributors"])

    def test_get_failure(self):
        response = self.client.get("/project/3/info")
        self.assertEqual(404, response.status_code)
        self.assertEqual({"detail":"No project with id 3 found"},
                         response.json())  
        
    def test_update(self):
        requestBody = {"updated_by": "janedoe",
                        "contributors": [2, 5]}
        response = self.client.put("/project/1/info", json = requestBody)

        self.assertEqual(200, response.status_code)
        responseAsDict = loads(response.json())
        self.assertIsNotNone(responseAsDict["updated_on"])
        self.assertEqual("janedoe", responseAsDict["updated_by"])
        self.assertEqual([2, 5], responseAsDict["contributors"])
    
    def test_update_invalid_body_value(self):
        invalidRequestBody = {"fake_property": 5}
        response = self.client.put("/project/1/info", json = invalidRequestBody)
        self.assertEqual(422, response.status_code)
    
    def test_update_empty_body(self):
        response = self.client.put("/project/1/info")
        self.assertEqual(422, response.status_code)

    def test_update_non_existing_project(self):
        requestBody = {"updated_by": "janedoe",
                        "contributors": [2, 5]} 
        response = self.client.put("/project/65/info", json = requestBody)
        self.assertEqual(404, response.status_code)
        self.assertEqual({"detail":"No project with id 65 found"},
                         response.json())    

    def delete_fail(self):
        response = self.client.delete("/project/5")
        self.assertEqual(404, response.status_code)
        self.assertEqual({"detail":"No project with id 5 found"},
                         response.json())
        
    def delete(self):
        response = self.client.delete("/project/1")
        self.assertEqual(204, response.status_code)