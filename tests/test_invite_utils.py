import unittest
from fastapi import HTTPException
from src.services.auth_utils import write_new_user
from src.services.invite_utils import decode_join_token, get_user_from_email, create_join_token
from src.services.project_manager_tables import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from src.routers.auth.schemas import User


class Test_Invite_Utils(unittest.TestCase):
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
        # create one user for test purposes
        test_user = User(username="username1",
                         full_name="Test User",
                         email="test@gmail.com",
                         password="1234")
        write_new_user(cls.session, test_user)
        cls.join_token = str()
        return super().setUpClass()
    
    @classmethod
    def tearDownClass(cls) -> None:
        cls.engine.dispose()
        return super().tearDownClass()
    

    def test_a_get_user_from_email(self):
        user = get_user_from_email(email="test@gmail.com", db=self.session)
        self.assertEqual("username1", user)
        self.assertRaises(HTTPException, get_user_from_email, "fake@gmail.com", self.session)


    def test_b_create_join_token(self):
        data = {"sub": "username1", "project": 1}
        token = create_join_token(to_encode=data)
        self.__class__.join_token = token
        self.assertIsInstance(self.join_token, str)
        self.assertNotEqual(0, len(token))
    
    def test_c_decode_join_token(self):
        username, project = decode_join_token(token=self.join_token,
                                              db=self.session)
        self.assertEqual("username1", username)
        self.assertEqual(1, project)
        
