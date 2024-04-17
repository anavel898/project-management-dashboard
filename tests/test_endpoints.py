import unittest

from fastapi.testclient import TestClient

from src.routers.project.projects import get_db

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from src.services.database import Base
from src.main import app

# SQLALCHEMY_DATABASE_URL = "sqlite://"

# engine = create_engine(
#     SQLALCHEMY_DATABASE_URL,
#     connect_args={"check_same_thread": False},
#     poolclass=StaticPool
# )
# TestingSessionLocal = sessionmaker(autocommit=False,
#                                    autoflush=False,
#                                    bind=engine)


# Base.metadata.create_all(bind=engine)


# def override_get_db():
#     try:
#         db = TestingSessionLocal()
#         yield db
#     finally:
#         db.close()


# app.dependency_overrides[get_db] = override_get_db

class TestEndpoints(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls) -> None:
        engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
        )
        TestingSessionLocal = sessionmaker(autocommit=False,
                                   autoflush=False,
                                   bind=engine)
        Base.metadata.create_all(bind=engine)
        app.dependency_overrides[get_db] = lambda: TestingSessionLocal() #override_get_db
        cls.client = TestClient(app)
        return super().setUpClass()


    def test_create(self):
        requestBody = {"name": "Project 1",
                        "created_by": "anavel",
                        "description": "toy description 1"}
        response = self.client.post("/projects", json=requestBody)
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

    def test_get_all(self):
        response = self.client.get("/projects")
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

    def test_get_failure(self):
        response = self.client.get("/project/3/info")
        self.assertEqual(404, response.status_code)
        self.assertEqual({"detail":"No project with id 3 found"},
                         response.json())
        
    def test_update(self):
        requestBody = {"updated_by": "janedoe",
                        "description": "updated description"}
        response = self.client.put("/project/1/info", json=requestBody)

        self.assertEqual(200, response.status_code)
        responseAsDict = dict(response.json())
        self.assertIsNotNone(responseAsDict["updated_on"])
        self.assertEqual("janedoe", responseAsDict["updated_by"])
        self.assertEqual("updated description", responseAsDict["description"])
    
    def test_update_invalid_body_value(self):
        invalidRequestBody = {"fake_property": 5}
        response = self.client.put("/project/1/info", json = invalidRequestBody)
        self.assertEqual(422, response.status_code)
    
    def test_update_empty_body(self):
        response = self.client.put("/project/1/info")
        self.assertEqual(422, response.status_code)

    def test_update_non_existing_project(self):
        requestBody = {"updated_by": "janedoe",
                        "description": "updated description"} 
        response = self.client.put("/project/65/info", json = requestBody)
        self.assertEqual(404, response.status_code)
        self.assertEqual({"detail":"No project with id 65 found"},
                         response.json())    

    def delete_fail(self):
        response = self.client.delete("/project/5999")
        self.assertEqual(404, response.status_code)
        self.assertEqual({"detail":"No project with id 5999 found"},
                         response.json())
        
    def delete(self):
        response = self.client.delete("/project/1")
        self.assertEqual(204, response.status_code)
