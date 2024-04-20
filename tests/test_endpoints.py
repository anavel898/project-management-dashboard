import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from src.dependecies import get_db
from src.services.project_manager_tables import Base
from src.main import app


class TestEndpoints(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls) -> None:
        # create in memory test db
        engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
        )
        TestingSessionLocal = sessionmaker(autocommit=False,
                                   autoflush=False,
                                   bind=engine)
        # create tables for needed mapped classes
        Base.metadata.create_all(bind=engine)
        # override the dependency providing db connection
        app.dependency_overrides[get_db] = lambda: TestingSessionLocal()
        # patch the function giving db connection to middleware
        cls.patcher = patch("src.main.get_session")
        cls.mock_function = cls.patcher.start()
        cls.mock_function.return_value = TestingSessionLocal()
        # create instance of app
        cls.client = TestClient(app)
        # create first user
        sign_up_data = {"username": "anavel",
                "full_name": "Ana",
                "email": "anavel@gmail.com",
                "password": "1234"}
        cls.client.post("/auth", data=sign_up_data)
        # login first user
        log_in_data = {
            "username": "anavel",
            "password": "1234"
        }
        response = cls.client.post("/login", data=log_in_data)
        response_as_dict = dict(response.json())
        cls.first_jwt = response_as_dict["access_token"]
        return super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.patcher.stop()
        return super().tearDownClass()
    
    def test_create(self):
        requestBody = {"name": "Project 1",
                        "description": "toy description 1"}
        header = {"Authorization": f"bearer {self.first_jwt}"}
        response = self.client.post("/projects", json=requestBody, headers=header)
        self.assertEqual(200, response.status_code)
        responseAsDict = dict(response.json())
        self.assertEqual(10, len(responseAsDict))
        self.assertEqual("Project 1", responseAsDict["name"])
        self.assertEqual(1, responseAsDict["id"])
        self.assertEqual("toy description 1", responseAsDict["description"])
        self.assertEqual("anavel", responseAsDict["created_by"])
        self.assertIsNotNone(responseAsDict["created_on"])
        self.assertIsNone(responseAsDict["logo"])
        self.assertIsNone(responseAsDict["updated_by"])
        self.assertIsNone(responseAsDict["updated_on"])
        self.assertEqual([], responseAsDict["documents"])
        self.assertEqual(['anavel'], responseAsDict["contributors"])

    #@unittest.skip("not adjusted for middleware yet")
    def test_get_all(self):
        header = {"Authorization": f"bearer {self.first_jwt}"}
        response = self.client.get("/projects", headers=header)
        self.assertEqual(200, response.status_code)
        # checking if project details are transferred appropriately
        response_payload = response.json()
        self.assertEqual(1, len(response_payload))
        self.assertIsInstance(response_payload[0], dict)
        self.assertEqual("Project 1", response_payload[0]["name"])
        self.assertEqual(1, response_payload[0]["id"])
        self.assertEqual("toy description 1",
                         response_payload[0]["description"])
        self.assertEqual("anavel", response_payload[0]["created_by"])
        self.assertIsNotNone(response_payload[0]["created_on"])
        self.assertIsNone(response_payload[0]["logo"])
        self.assertIsNone(response_payload[0]["updated_by"])
        self.assertIsNone(response_payload[0]["updated_on"])
        self.assertEqual([], response_payload[0]["documents"])
        self.assertEqual(['anavel'], response_payload[0]["contributors"])
        
    @unittest.skip("not adjusted for middleware yet")
    def test_get(self):
        response = self.client.get("/project/1/info")
        self.assertEqual(200, response.status_code)
        # checking if project details are transferred appropriately
        responseAsDict = dict(response.json())
        self.assertEqual(10, len(responseAsDict))
        self.assertEqual("Project 1", responseAsDict["name"])
        self.assertEqual(1, responseAsDict["id"])
        self.assertEqual("toy description 1", responseAsDict["description"])
        self.assertEqual("anavel", responseAsDict["created_by"])
        self.assertIsNotNone(responseAsDict["created_on"])
        self.assertIsNone(responseAsDict["logo"])
        self.assertIsNone(responseAsDict["updated_by"])
        self.assertIsNone(responseAsDict["updated_on"])
        self.assertEqual([], responseAsDict["documents"])
        self.assertEqual(['anavel'], responseAsDict["contributors"])

    @unittest.skip("not adjusted for middleware yet")
    def test_get_failure(self):
        response = self.client.get("/project/3/info")
        self.assertEqual(404, response.status_code)
        self.assertEqual({"detail":"No project with id 3 found"},
                         response.json())

    @unittest.skip("not adjusted for middleware yet")    
    def test_update(self):
        requestBody = {"updated_by": "janedoe",
                        "description": "updated description"}
        response = self.client.put("/project/1/info", json=requestBody)

        self.assertEqual(200, response.status_code)
        responseAsDict = dict(response.json())
        self.assertIsNotNone(responseAsDict["updated_on"])
        self.assertEqual("janedoe", responseAsDict["updated_by"])
        self.assertEqual("updated description", responseAsDict["description"])
    
    @unittest.skip("not adjusted for middleware yet")
    def test_update_invalid_body_value(self):
        invalidRequestBody = {"fake_property": 5}
        response = self.client.put("/project/1/info", json = invalidRequestBody)
        self.assertEqual(422, response.status_code)
    
    @unittest.skip("not adjusted for middleware yet")
    def test_update_empty_body(self):
        response = self.client.put("/project/1/info")
        self.assertEqual(422, response.status_code)

    @unittest.skip("not adjusted for middleware yet")
    def test_update_non_existing_project(self):
        requestBody = {"updated_by": "janedoe",
                        "description": "updated description"} 
        response = self.client.put("/project/65/info", json = requestBody)
        self.assertEqual(404, response.status_code)
        self.assertEqual({"detail":"No project with id 65 found"},
                         response.json())    

    @unittest.skip("not adjusted for middleware yet")
    def delete_fail(self):
        response = self.client.delete("/project/5999")
        self.assertEqual(404, response.status_code)
        self.assertEqual({"detail":"No project with id 5999 found"},
                         response.json())
    
    @unittest.skip("not adjusted for middleware yet")   
    def delete(self):
        response = self.client.delete("/project/1")
        self.assertEqual(204, response.status_code)
