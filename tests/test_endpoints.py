import unittest
from unittest.mock import patch
from fastapi import HTTPException
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
        sign_up_data = {"username": "johdoe",
                "full_name": "John Doe",
                "email": "johdoe@gmail.com",
                "password": "1234"}
        cls.client.post("/auth", data=sign_up_data)
        # login first user
        log_in_data = {
            "username": "johdoe",
            "password": "1234"
        }
        response = cls.client.post("/login", data=log_in_data)
        response_as_dict = dict(response.json())
        cls.jon_jwt = response_as_dict["access_token"]
        return super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.patcher.stop()
        return super().tearDownClass()


    def test_a_middleware(self):
        def call_something_wo_auth_header():
            try:
                self.client.get("/projects")
            except HTTPException as ex:
                code = ex.status_code
                detail = ex.detail
                return code, detail
        expected_code, expected_detail = call_something_wo_auth_header()
        self.assertEqual(400, expected_code)
        self.assertEqual("No Authorization header", expected_detail)

    def test_b1_new_user(self):
        sign_up_data = {"username": "jandoe",
                "full_name": "Jane Doe",
                "email": "jandoe@gmail.com",
                "password": "1234"}
        response = self.client.post("/auth", data=sign_up_data)
        self.assertEqual(200, response.status_code)
        self.assertEqual(sign_up_data["username"], response.json()["username"])
        self.assertEqual(sign_up_data["full_name"], response.json()["full_name"])
        self.assertEqual(sign_up_data["email"], response.json()["email"])


    def test_b2_new_user_400_error(self):
        sign_up_data = {"username": "jandoe",
                "full_name": "Jane Doe",
                "email": "jandoe@gmail.com",
                "password": "1234"}
        response = self.client.post("/auth", data=sign_up_data)
        self.assertEqual(400, response.status_code)
        self.assertEqual({"detail": "Username 'jandoe' is already taken"},
                         response.json())

    
    def test_c1_login_new_user(self):
        log_in_data = {
            "username": "jandoe",
            "password": "1234"
        }
        response = self.client.post("/login", data=log_in_data)
        self.assertEqual(200, response.status_code)
        response_as_dict = dict(response.json())
        self.assertEqual("bearer", response_as_dict["token_type"])
        self.assertIsInstance(response_as_dict["access_token"], str)

    
    def test_c2_login_failure(self):
        log_in_data = {
            "username": "jandoe",
            "password": "wrong password"
        }
        response = self.client.post("/login", data=log_in_data)
        self.assertEqual(401, response.status_code)
        self.assertEqual("Incorrect username or password", dict(response.json())["detail"])


    def test_d_create(self):
        request_body = {"name": "Project 1",
                        "description": "toy description 1"}
        header = {"Authorization": f"bearer {self.jon_jwt}"}
        response = self.client.post("/projects", json=request_body, headers=header)
        self.assertEqual(200, response.status_code)
        response_as_dict = dict(response.json())
        self.assertEqual(10, len(response_as_dict))
        self.assertEqual("Project 1", response_as_dict["name"])
        self.assertEqual(1, response_as_dict["id"])
        self.assertEqual("toy description 1", response_as_dict["description"])
        self.assertEqual("johdoe", response_as_dict["created_by"])
        self.assertIsNotNone(response_as_dict["created_on"])
        self.assertIsNone(response_as_dict["logo"])
        self.assertIsNone(response_as_dict["updated_by"])
        self.assertIsNone(response_as_dict["updated_on"])
        self.assertEqual([], response_as_dict["documents"])
        self.assertEqual(['johdoe'], response_as_dict["contributors"])


    def test_e_get_all(self):
        # login as Jane
        log_in_data = {
            "username": "jandoe",
            "password": "1234"
        }
        login_response = self.client.post("/login", data=log_in_data)
        jane_jwt = dict(login_response.json())["access_token"]
        # create project as Jane
        request_body = {"name": "Jane's",
                        "description": "toy description"}
        self.client.post("/projects",
                         json=request_body,
                         headers={"Authorization": f"bearer {jane_jwt}"})

        # calling method as John
        header = {"Authorization": f"bearer {self.jon_jwt}"}
        response = self.client.get("/projects", headers=header)
        response_payload = response.json()
        self.assertEqual(200, response.status_code)
        # checking that only John's project is returned
        self.assertEqual(1, len(response_payload))
        self.assertIsInstance(response_payload[0], dict)
        self.assertEqual("Project 1", response_payload[0]["name"])
        self.assertEqual(1, response_payload[0]["id"])
        self.assertEqual("toy description 1",
                         response_payload[0]["description"])
        #self.assertEqual("johdoe", response_payload[0]["created_by"])
        self.assertEqual("johdoe", response_payload[0]["owner"])
        self.assertIsNotNone(response_payload[0]["created_on"])
        # self.assertIsNone(response_payload[0]["logo"])
        # self.assertIsNone(response_payload[0]["updated_by"])
        # self.assertIsNone(response_payload[0]["updated_on"])
        # self.assertEqual([], response_payload[0]["documents"])
        # self.assertEqual(['johdoe'], response_payload[0]["contributors"])

    
    def test_f_get(self):
        header = {"Authorization": f"bearer {self.jon_jwt}"}
        response = self.client.get("/project/1/info", headers=header)
        self.assertEqual(200, response.status_code)
        # checking if project details are transferred appropriately
        response_as_dict = dict(response.json())
        self.assertEqual(10, len(response_as_dict))
        self.assertEqual("Project 1", response_as_dict["name"])
        self.assertEqual(1, response_as_dict["id"])
        self.assertEqual("toy description 1", response_as_dict["description"])
        self.assertEqual("johdoe", response_as_dict["created_by"])
        self.assertIsNotNone(response_as_dict["created_on"])
        self.assertIsNone(response_as_dict["logo"])
        self.assertIsNone(response_as_dict["updated_by"])
        self.assertIsNone(response_as_dict["updated_on"])
        self.assertEqual([], response_as_dict["documents"])
        self.assertEqual(['johdoe'], response_as_dict["contributors"])

    
    def test_f_get_404_failure(self):
        header = {"Authorization": f"bearer {self.jon_jwt}"}
        response = self.client.get("/project/45/info", headers=header)
        self.assertEqual(404, response.status_code)
        self.assertEqual({"detail":"No project with id 45 found"},
                         response.json())

       
    def test_f_get_403_failure(self):
        # login as Jane and try to access John's project
        log_in_data = {
            "username": "jandoe",
            "password": "1234"
        }
        response = self.client.post("/login", data=log_in_data)
        jane_jwt = dict(response.json())["access_token"]
        header = {"Authorization": f"bearer {jane_jwt}"}
        get_response = self.client.get("/project/1/info", headers=header)
        self.assertEqual(403, get_response.status_code)
        self.assertEqual({"detail": "You don't have access to this project."},
                         get_response.json())
       
    
    def test_g_update(self):
        request_body = {"description": "updated description"}
        header = {"Authorization": f"bearer {self.jon_jwt}"}
        response = self.client.put("/project/1/info", json=request_body, headers=header)
        self.assertEqual(200, response.status_code)
        response_as_dict = dict(response.json())
        self.assertIsNotNone(response_as_dict["updated_on"])
        self.assertEqual("johdoe", response_as_dict["updated_by"])
        self.assertEqual("updated description", response_as_dict["description"])
    
    
    def test_g_update_422_failure(self):
        invalid_request_body = {"fake_property": 5}
        header = {"Authorization": f"bearer {self.jon_jwt}"}
        response = self.client.put("/project/1/info", json=invalid_request_body, headers=header)
        self.assertEqual(422, response.status_code)
    
    
    def test_g_update_404_failure(self):
        request_body = {"description": "updated description"}
        header = {"Authorization": f"bearer {self.jon_jwt}"}
        response = self.client.put("/project/65/info", json=request_body, headers=header)
        self.assertEqual(404, response.status_code)
        self.assertEqual({"detail":"No project with id 65 found"},
                         response.json())

    
    def test_g_update_403_failure(self):
        log_in_data = {
            "username": "jandoe",
            "password": "1234"
        }
        login_response = self.client.post("/login", data=log_in_data)
        jane_jwt = dict(login_response.json())["access_token"]
        header = {"Authorization": f"bearer {jane_jwt}"}
        request_body = {"description": "updated description"}
        response = self.client.put("/project/1/info", json=request_body,
                                   headers=header)
        self.assertEqual(403, response.status_code)
        self.assertEqual({"detail": "You don't have access to this project."},
                         response.json())
        
    
    def test_h1_grant_access(self):
        header = {"Authorization": f"bearer {self.jon_jwt}"}
        request_body = {"name": "jandoe"}
        response = self.client.post("/project/1/invite",
                                    json=request_body,
                                    headers=header)
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, response.json()["project_id"])
        self.assertEqual("participant", response.json()["role"])
        self.assertEqual("jandoe", response.json()["username"])
        # now jane should be able to get project 1
        log_in_data = {
            "username": "jandoe",
            "password": "1234"
        }
        login_response = self.client.post("/login", data=log_in_data)
        jane_jwt = dict(login_response.json())["access_token"]
        jane_header = {"Authorization": f"bearer {jane_jwt}"}
        get_response = self.client.get("/project/1/info", headers=jane_header)
        self.assertEqual(200, get_response.status_code)

    
    def test_h2_grant_access_403_fail(self):
        log_in_data = {
            "username": "jandoe",
            "password": "1234"
        }
        login_response = self.client.post("/login", data=log_in_data)
        jane_jwt = dict(login_response.json())["access_token"]
        header = {"Authorization": f"bearer {jane_jwt}"}
        request_body = {"name": "petpet"}
        response = self.client.post("/project/1/invite",
                                    json=request_body,
                                    headers=header)
        self.assertEqual(403, response.status_code)
        self.assertEqual({"detail": "Only project owners can perform this action."},
                         response.json())

    
    def test_z_delete_404_fail(self):
        header = {"Authorization": f"bearer {self.jon_jwt}"}
        response = self.client.delete("/project/5999", headers=header)
        self.assertEqual(404, response.status_code)
        self.assertEqual({"detail":"No project with id 5999 found"},
                         response.json())

    
    def test_z_delete_403_fail(self):
        log_in_data = {
            "username": "jandoe",
            "password": "1234"
        }
        login_response = self.client.post("/login", data=log_in_data)
        jane_jwt = dict(login_response.json())["access_token"]
        header = {"Authorization": f"bearer {jane_jwt}"}
        response = self.client.delete("/project/1", headers=header)
        self.assertEqual(403, response.status_code)
        self.assertEqual({"detail": "Only project owners can perform this action."},
                         response.json())
    
      
    def test_z_delete(self):
        header = {"Authorization": f"bearer {self.jon_jwt}"}
        request_body = {"name": "Project for testing delete",
                        "description": "toy description"}
        header = {"Authorization": f"bearer {self.jon_jwt}"}
        post_response = self.client.post("/projects", json=request_body, headers=header)
        created_id = dict(post_response.json())["id"]
        response = self.client.delete(f"/project/{created_id}", headers=header)
        self.assertEqual(200, response.status_code)

       