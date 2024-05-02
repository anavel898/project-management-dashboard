import unittest
from fastapi import HTTPException
from src.services.auth_utils import write_new_user, authenticate_user, create_access_token, check_privilege
from src.services.project_manager_tables import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from src.routers.auth.schemas import User


class Test_Auth_Utils(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
        )
        cls.session = Session(bind=engine, autoflush=False, autocommit=False)
        Base.metadata.create_all(bind=engine)
        cls.engine = engine
        return super().setUpClass()
    
    @classmethod
    def tearDownClass(cls) -> None:
        cls.engine.dispose()
        return super().tearDownClass()
    

    def test_a_write_new_user(self):
        new_test_user = User(username="username1",
                             full_name="Test User",
                             email="test@gmail.com",
                             password="1234")
        user = write_new_user(db=self.session, user=new_test_user)
        self.assertEqual("username1", user.username)
        self.assertEqual("Test User", user.full_name)
        self.assertEqual("test@gmail.com", user.email)

    
    def test_b_authenticate_user(self):
        wrong_username_resp = authenticate_user(self.session, "fakeUser", "1234")
        self.assertFalse(wrong_username_resp)
        wrong_password_resp = authenticate_user(self.session, "username1", "14")
        self.assertFalse(wrong_password_resp)
        correct_info = authenticate_user(self.session, "username1", "1234")
        self.assertEqual("username1", correct_info.username)


    def test_c_create_access_token(self):
        data = {"sub": "username1"}
        token = create_access_token(data=data)
        self.assertIsInstance(token, str)
    

    def test_d_check_privilege(self):
        self.assertRaises(HTTPException, check_privilege, 6, [1,3], [2,5])
        self.assertRaises(HTTPException, check_privilege, 1, [3], [1,2,5], True)
        