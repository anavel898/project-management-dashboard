from datetime import datetime
import os
import unittest
from unittest import mock
from uuid import uuid4

from fastapi import HTTPException
from src.services.auth_utils import write_new_user
from src.services.project_manager_tables import Base, Documents
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from src.routers.auth.schemas import User
from src.services.db_project_handler import DbProjectHandler
from src.services.document_handler import DocumentHandler


class Test_Document_Handler(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
        )
        cls.session = Session(bind=engine, autoflush=False, autocommit=False)
        Base.metadata.create_all(bind=engine)
        # create test user
        test_user = User(username="username1",
                         full_name="Test User",
                         email="test@gmail.com",
                         password="1234")
        write_new_user(cls.session, test_user)
        cls.engine = engine
        # create test project
        proj_handler = DbProjectHandler()
        proj_handler.create(name="Project 1",
                            created_by="username1",
                            description="toy description",
                            db=cls.session)
        with open("toy_file.txt", 'w') as f:
            pass
        # create first document
        uuid = uuid4()
        new_document = Documents(name="toy_file.txt",
                                 project_id=1,
                                 added_by="username1",
                                 content_type="text/plain",
                                 s3_key=str(uuid),
                                 added_on=datetime.now())
        cls.session.add(new_document)
        cls.session.commit()
        return super().setUpClass()
    

    @classmethod
    def tearDownClass(cls) -> None:
        cls.engine.dispose()
        os.remove("./toy_file.txt")
        return super().tearDownClass()
    

    def test_a_get_document_project(self):
        doc_proj = DocumentHandler.get_document_project(document_id=1,
                                                        db=self.session)
        self.assertEqual(1, doc_proj)
        self.assertRaises(HTTPException,
                          DocumentHandler.get_document_project,
                          5,
                          self.session)
        

    @mock.patch("src.services.document_handler.S3Service.download_file_from_s3", return_value=bytes("random_string", "utf-8"))
    def test_b_download_document(self, result):
        name, content_type, contents = DocumentHandler.download_document(1, self.session)
        self.assertTrue(result.called)
        self.assertEqual("toy_file.txt", name)
        self.assertEqual("text/plain", content_type)
        self.assertEqual(bytes("random_string", "utf-8"), contents)


    @mock.patch("src.services.document_handler.S3Service.upload_file_to_s3")
    def test_c_update_document(self, result):
        with open("toy_file_2.txt", 'w') as f:
            pass
        file_contents = open("./toy_file_2.txt", "rb")
        timestamp = datetime.now()
        updated_doc = DocumentHandler.update_document(document_id=1,
                                                      doc_name="toy_file_2.txt",
                                                      content_type="text/plain",
                                                      updating_user="username1",
                                                      b_content=file_contents,
                                                      db=self.session)
        file_contents.close()
        os.remove("./toy_file_2.txt")
        self.assertTrue(result.called)
        self.assertEqual(1, updated_doc.id)
        self.assertEqual("toy_file_2.txt", updated_doc.name)
        self.assertEqual("username1", updated_doc.added_by)
        self.assertEqual(1, updated_doc.project_id)
        self.assertLessEqual(timestamp, updated_doc.added_on)
        self.assertEqual("text/plain", updated_doc.content_type)


    @mock.patch("src.services.document_handler.S3Service.delete_file_from_s3")
    def test_d_delete_document(self, result):
        DocumentHandler.delete_document(1, self.session)
        self.assertTrue(result.called)
        self.assertIsNone(self.session.get(Documents, 1))
