import os
import unittest
from unittest import mock
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from src.dependecies import get_db
from datetime import datetime
from src.services.project_manager_tables import Base
from src.main import app


def image_helper():
    m = MagicMock()
    with open("./tests/test_logo.png", "rb") as image:
        content = image.read()
        m.return_value = content
    return m

def email_helper():
    m = MagicMock()
    m.return_value = "str-simulating-message-id"
    return m


class Test_Endpoints(unittest.TestCase):
    
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
        # creating toy file to use for tests
        with open("toy_file.txt", 'w') as f:
            pass
        cls.join_token = ""
        cls.engine = engine
        return super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.patcher.stop()
        os.remove("./toy_file.txt")
        cls.engine.dispose()
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
        self.assertEqual("johdoe", response_payload[0]["owner"])
        self.assertIsNotNone(response_payload[0]["created_on"])

    
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
        response = self.client.post("/project/1/invite", json=request_body, headers=header)
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

    
    @mock.patch("src.services.db_project_handler.S3Service.upload_file_to_s3")
    def test_i_upload_document(self, result):
        header = {"Authorization": f"bearer {self.jon_jwt}"}
        file_contents = open("./toy_file.txt", "rb")
        doc_file = {"upload_files":
                    ("toy_file.txt", file_contents, "text/plain")}
        timestamp = datetime.now()
        response = self.client.post("/project/1/documents",
                                    headers=header,
                                    files=doc_file)
        file_contents.close()
        self.assertEqual(200, response.status_code)
        self.assertTrue(result.called)
        self.assertEqual(1, len(response.json()))
        self.assertEqual(1, response.json()[0]["id"])
        self.assertEqual("toy_file.txt", response.json()[0]["name"])
        self.assertEqual("johdoe", response.json()[0]["added_by"])
        self.assertLessEqual(timestamp,
                             datetime.strptime(response.json()[0]["added_on"],
                                               '%Y-%m-%dT%H:%M:%S.%f'))
        self.assertEqual("text/plain", response.json()[0]["content_type"])

    
    def test_j_get_all_documents(self):
        header = {"Authorization": f"bearer {self.jon_jwt}"}
        response = self.client.get("/project/1/documents", headers=header)
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.json()))
        self.assertEqual(1, response.json()[0]["id"])
        self.assertEqual("toy_file.txt", response.json()[0]["name"])
        self.assertEqual("johdoe", response.json()[0]["added_by"])
        self.assertIsNotNone(response.json()[0]["added_on"])
        self.assertEqual("text/plain", response.json()[0]["content_type"])


    @mock.patch("src.services.document_handler.S3Service.download_file_from_s3", return_value=bytes("random_string", "utf-8"))
    def test_k_download_document(self, result):
        header = {"Authorization": f"bearer {self.jon_jwt}"}
        response = self.client.get("/document/1", headers=header)
        self.assertEqual(200, response.status_code)
        self.assertTrue(result.called)
        self.assertEqual("attachment;filename=toy_file.txt",
                         response.headers["content-disposition"])
        self.assertEqual("text/plain", response.headers["content-type"])
        self.assertEqual("13", response.headers["content-length"])
        self.assertEqual(bytes("random_string", "utf-8"), response.content) 

    
    @mock.patch("src.services.document_handler.S3Service.upload_file_to_s3")
    def test_l_update_document(self, result):
        header = {"Authorization": f"bearer {self.jon_jwt}"}
        with open("toy_file_2.txt", 'w') as f:
            pass
        file_contents = open("./toy_file.txt", "rb")
        doc_file = {"new_document":
                    ("toy_file_2.txt", file_contents, "text/plain")}
        timestamp = datetime.now()
        response = self.client.put("/document/1",
                                    headers=header,
                                    files=doc_file)
        file_contents.close()
        os.remove("./toy_file_2.txt")
        self.assertEqual(200, response.status_code)
        self.assertTrue(result.called)
        self.assertEqual(1, response.json()["id"])
        self.assertEqual("toy_file_2.txt", response.json()["name"])
        self.assertEqual("johdoe", response.json()["added_by"])
        self.assertLessEqual(timestamp,
                             datetime.strptime(response.json()["added_on"],
                                               '%Y-%m-%dT%H:%M:%S.%f'))
        self.assertEqual("text/plain", response.json()["content_type"])

       
    @mock.patch("src.services.document_handler.S3Service.delete_file_from_s3")
    def test_m_delete_document(self, result):
        header = {"Authorization": f"bearer {self.jon_jwt}"}
        response = self.client.delete("/document/1", headers=header)
        self.assertEqual(204, response.status_code)
        self.assertTrue(result.called)
        try_getting_doc = self.client.get("/document/1", headers=header)
        self.assertEqual(404, try_getting_doc.status_code)
        self.assertEqual({"detail":"No document with id 1 found"},
                         try_getting_doc.json())


    @mock.patch("src.services.db_project_handler.S3Service.upload_file_to_s3")
    def test_n1_upsert_logo(self, result):
        header = {"Authorization": f"bearer {self.jon_jwt}"}
        file_contents = open("./tests/test_logo.png", "rb")
        doc_file = {"logo":
                    ("test_logo.png", file_contents, "image/png")}
        timestamp = datetime.now()
        response = self.client.put("/project/1/logo",
                                    headers=header,
                                    files=doc_file)
        file_contents.close()
        self.assertEqual(200, response.status_code)
        self.assertTrue(result.called)
        self.assertEqual(1, response.json()["project_id"])
        self.assertEqual("test_logo.png", response.json()["logo_name"])
        self.assertEqual("johdoe", response.json()["uploaded_by"])
        self.assertLessEqual(timestamp,
                             datetime.strptime(response.json()["uploaded_on"],
                                               '%Y-%m-%dT%H:%M:%S.%f'))


    def test_n2_upsert_logo_400_fail(self):
        header = {"Authorization": f"bearer {self.jon_jwt}"}
        file_contents = open("./toy_file.txt", "rb")
        doc_file = {"logo":
                    ("test_logo.png", file_contents, "text/plain")}
        response = self.client.put("/project/1/logo",
                                    headers=header,
                                    files=doc_file)
        file_contents.close()
        self.assertEqual(400, response.status_code)
        self.assertEqual({"detail": "Logo must be a .png or .jpeg file"},
                         response.json())


    @mock.patch("src.services.db_project_handler.S3Service.download_file_from_s3", new_callable=image_helper)
    def test_o_download_logo(self, result):
        header = {"Authorization": f"bearer {self.jon_jwt}"}
        response = self.client.get("/project/1/logo", headers=header)
        image = bytes()
        with open("./tests/test_logo.png", "rb") as i:
            image = i.read()
        self.assertEqual(200, response.status_code)
        self.assertTrue(result.called)
        self.assertEqual("attachment;filename=test_logo.png",
                         response.headers["content-disposition"])
        self.assertEqual("application/octet-stream",
                         response.headers["content-type"])
        self.assertEqual(image, response.content)


    @mock.patch("src.services.db_project_handler.S3Service.delete_file_from_s3")
    def test_p_delete_logo(self, result):
        header = {"Authorization": f"bearer {self.jon_jwt}"}
        response = self.client.delete("/project/1/logo", headers=header)
        self.assertEqual(204, response.status_code)
        try_get_logo = self.client.get("/project/1/logo", headers=header)
        self.assertEqual(404, try_get_logo.status_code)
        self.assertEqual({"detail": "Project with id 1 doesn't have a logo"},
                         try_get_logo.json())


    @mock.patch("src.services.db_project_handler.SESService.send_email_via_ses", new_callable=email_helper)
    def test_q1_share_via_email(self, result):
        # create new user to invite
        sign_up_data = {"username": "jandoe1",
                        "full_name": "Jane Doe",
                        "email": "jandoe1@gmail.com",
                        "password": "1234"}
        self.client.post("/auth", data=sign_up_data)
        header = {"Authorization": f"bearer {self.jon_jwt}"}
        request_body = {"email": "jandoe1@gmail.com"}
        response = self.client.get("/project/1/share",
                                   params=request_body,
                                   headers=header)
        self.assertEqual(200, response.status_code)
        self.assertTrue(result.called)
        self.assertEqual("str-simulating-message-id",
                         response.json()["aws_message_id"])
        self.assertIsInstance(response.json()["join_token"], str)
        # save generated token for future use
        self.__class__.join_token = response.json()["join_token"]

    
    def test_q2_share_via_email_400_fail(self):
        header = {"Authorization": f"bearer {self.jon_jwt}"}
        request_body = {"email": "johdoe@gmail.com"}
        response = self.client.get("/project/1/share",
                                   params=request_body,
                                   headers=header)
        self.assertEqual(400, response.status_code)
        self.assertEqual({"detail": "Cannot invite yourself to project"},
                         response.json())
        
    
    def test_q3_share_via_email_400_fail_2(self):
        header = {"Authorization": f"bearer {self.jon_jwt}"}
        request_body = {"email": "fake_user_email@gmail.com"}
        response = self.client.get("/project/1/share",
                                   params=request_body,
                                   headers=header)
        self.assertEqual(400, response.status_code)
        self.assertEqual({"detail": "No users are registered with provided email address"},
                         response.json())


    def test_r_join_via_invite(self):
        request_params = {"project_id": 1, "join_token": self.join_token}
        response = self.client.get("/join", params=request_params)
        self.assertEqual(200, response.status_code)
        self.assertEqual("participant", response.json()["role"])
        self.assertEqual(1, response.json()["project_id"])
        self.assertEqual("jandoe1", response.json()["username"])

    
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
        self.assertEqual(204, response.status_code)
