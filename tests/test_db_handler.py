from datetime import datetime
import os
import unittest
from unittest import mock

from fastapi import HTTPException
from src.services.auth_utils import write_new_user
from src.services.project_manager_tables import Base, Projects
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from src.routers.auth.schemas import User
from src.services.db_project_handler import DbProjectHandler
from dotenv import load_dotenv


def image_helper():
    m = mock.MagicMock()
    with open("./tests/test_logo.png", "rb") as image:
        content = image.read()
        m.return_value = content
    return m

def email_helper():
    m = mock.MagicMock()
    m.return_value = "str-simulating-message-id"
    return m


class Test_Db_Handler(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
        )
        cls.session = Session(bind=engine, autoflush=False, autocommit=False)
        Base.metadata.create_all(bind=engine)
        test_user = User(username="username1",
                         full_name="Test User",
                         email="test@gmail.com",
                         password="1234")
        write_new_user(cls.session, test_user)
        cls.engine = engine
        with open("toy_file.txt", 'w') as f:
            pass
        return super().setUpClass()
    
    @classmethod
    def tearDownClass(cls) -> None:
        cls.engine.dispose()
        os.remove("./toy_file.txt")
        return super().tearDownClass()
    

    def test_a_constructor(self):
        handler = DbProjectHandler()
        load_dotenv()
        self.assertEqual(os.getenv("RAW_LOGO_BUCKET"),
                         handler.raw_logos_bucket)
        self.assertEqual(os.getenv("RESIZED_LOGO_BUCKET"),
                         handler.processed_logos_bucket)
        self.assertEqual(os.getenv("DOCUMENTS_BUCKET"),
                         handler.documents_bucket)


    def test_b_create(self):
        handler = DbProjectHandler()
        new_proj = handler.create(name="Project 1",
                                  created_by="username1",
                                  description="toy description",
                                  db=self.session)
        self.assertEqual("Project 1", new_proj.name)
        self.assertEqual(1, new_proj.id)
        self.assertEqual("toy description", new_proj.description)
        self.assertEqual("username1", new_proj.created_by)
        self.assertIsNotNone(new_proj.created_on)
        self.assertIsNone(new_proj.logo)
        self.assertIsNone(new_proj.updated_by)
        self.assertIsNone(new_proj.updated_on)
        self.assertEqual([], new_proj.documents)
        self.assertEqual(['username1'], new_proj.contributors)

    
    def test_b_get(self):
        handler = DbProjectHandler()
        proj = handler.get(project_id=1, db=self.session)
        self.assertEqual("Project 1", proj.name)
        self.assertEqual(1, proj.id)
        self.assertEqual("toy description", proj.description)
        self.assertEqual("username1", proj.created_by)
        self.assertIsNotNone(proj.created_on)
        self.assertIsNone(proj.logo)
        self.assertIsNone(proj.updated_by)
        self.assertIsNone(proj.updated_on)
        self.assertEqual([], proj.documents)
        self.assertEqual(['username1'], proj.contributors)


    def test_c_get_all(self):
        handler = DbProjectHandler()
        handler.create(name="Project 2",
                       created_by="username1",
                       description="toy description",
                       db=self.session)
        all_projs = handler.get_all(db=self.session, accessible_projects=[1, 2])
        self.assertEqual(2, len(all_projs))
        self.assertEqual("Project 1", all_projs[0].name)
        self.assertEqual(1, all_projs[0].id)
        self.assertEqual("toy description", all_projs[0].description)
        self.assertEqual("username1", all_projs[0].owner)
        self.assertIsNotNone(all_projs[0].created_on)

    
    def test_d_update_info(self):
        handler = DbProjectHandler()
        details = {"description": "new description", "updated_by": "username1"}
        timestamp = datetime.now()
        proj = handler.update_info(project_id=1,
                            attributes_to_update=details,
                            db=self.session)
        self.assertEqual("Project 1", proj.name)
        self.assertEqual(1, proj.id)
        self.assertEqual("new description", proj.description)
        self.assertEqual("username1", proj.created_by)
        self.assertIsNotNone(proj.created_on)
        self.assertIsNone(proj.logo)
        self.assertEqual('username1', proj.updated_by)
        self.assertLessEqual(timestamp, proj.updated_on)
        self.assertEqual([], proj.documents)
        self.assertEqual(['username1'], proj.contributors)
    

    def test_e_get_project_internal(self):
        handler = DbProjectHandler()
        proj = handler.get_project_internal(1, self.session)
        self.assertIsNotNone(proj)
        self.assertRaises(HTTPException, handler.get_project_internal, 5, self.session)


    def test_f_grant_access(self):
        # create new user to grant access to
        new_user = User(username="username2",
                         full_name="New User",
                         email="new@gmail.com",
                         password="1234")
        write_new_user(self.session, new_user)
        # test method
        handler = DbProjectHandler()
        new_permission = handler.grant_access(1, "username2", self.session)
        self.assertEqual(1, new_permission.project_id)
        self.assertEqual("username2", new_permission.username)
        self.assertEqual("participant", new_permission.role)


    def test_g_get_project_privileges(self):
        owned, participating = DbProjectHandler.get_project_privileges(self.session, "username1")
        self.assertEqual([], participating)
        self.assertEqual([1, 2], owned)
        owned_2, participating_2 = DbProjectHandler.get_project_privileges(self.session, "username2")
        self.assertEqual([], owned_2)
        self.assertEqual([1], participating_2)


    @mock.patch("src.services.db_project_handler.S3Service.upload_file_to_s3")
    def test_h_associate_document(self, result):
        handler = DbProjectHandler()
        file_contents = open("./toy_file.txt", "rb")
        timestamp = datetime.now()
        doc = handler.associate_document(project_id=1,
                                         doc_name="toy_file.txt",
                                         content_type="text/plain",
                                         caller="username1",
                                         byfile=file_contents,
                                         db=self.session)
        file_contents.close()
        self.assertTrue(result.called)
        self.assertEqual(1,doc.id)
        self.assertEqual("toy_file.txt", doc.name)
        self.assertEqual("username1", doc.added_by)
        self.assertLessEqual(timestamp, doc.added_on)
        self.assertEqual("text/plain", doc.content_type)


    def test_i_get_docs(self):
        handler = DbProjectHandler()
        all_docs = handler.get_docs(1, self.session)
        self.assertEqual(1, len(all_docs))
        self.assertEqual(1, all_docs[0].id)
        self.assertEqual("toy_file.txt", all_docs[0].name)
        self.assertEqual("username1", all_docs[0].added_by)
        self.assertIsInstance(all_docs[0].added_on, datetime)
        self.assertEqual("text/plain", all_docs[0].content_type)

    
    @mock.patch("src.services.db_project_handler.S3Service.upload_file_to_s3")
    def test_j_upload_logo(self, result):
        handler = DbProjectHandler()
        file_contents = open("./tests/test_logo.png", "rb")
        timestamp = datetime.now()
        logo = handler.upload_logo(project_id=1,
                                   logo_name="test_logo.png",
                                   b_content=file_contents,
                                   logo_poster="username1",
                                   content_type="image/png",
                                   db=self.session)
        file_contents.close()
        self.assertTrue(result.called)
        self.assertEqual(1, logo.project_id)
        self.assertEqual("test_logo.png", logo.logo_name)
        self.assertEqual("username1", logo.uploaded_by)
        self.assertLessEqual(timestamp, logo.uploaded_on)


    @mock.patch("src.services.db_project_handler.S3Service.download_file_from_s3", new_callable=image_helper)
    def test_k_download_logo(self, result):
        handler = DbProjectHandler()
        name, content = handler.download_logo(project_id=1, db=self.session)
        image = bytes()
        with open("./tests/test_logo.png", "rb") as i:
            image = i.read()
        self.assertTrue(result.called)
        self.assertEqual("test_logo.png", name)
        self.assertEqual(image, content)


    @mock.patch("src.services.db_project_handler.S3Service.delete_file_from_s3")
    def test_l_delete_logo(self, result):
        handler = DbProjectHandler()
        handler.delete_logo(project_id=1,
                            user_calling="username2",
                            db=self.session)
        self.assertTrue(result.called)
        proj = self.session.get(Projects, 1)
        self.assertIsNone(proj.logo)
        self.assertEqual("username2", proj.updated_by)
        self.assertIsInstance(proj.updated_on, datetime)


    def test_m_email_invite(self):
        handler = DbProjectHandler()
        email_text, join_token = handler.email_invite(project_id=1,
                                                      invite_sender_username="username1",
                                                      invite_receiver="username2",
                                                      email="new@gmail.com",
                                                      db=self.session)
        desired_text = f"""Hello,
        Test User invited you to join the project 'Project 1'.
        To accept the invite go to: http://<url-where-app-is-running>/join?project_id=1&join_token={join_token}
        This invite is valid for 3 days. This is an automatic email, do not reply to this address. For additional info reply to test@gmail.com"""
        self.assertEqual(desired_text, email_text)
        self.assertIsInstance(join_token, str)


    def test_z_delete(self):
        handler = DbProjectHandler()
        handler.delete(project_id=1, db=self.session)
        self.assertIsNone(self.session.get(Projects, 1))
