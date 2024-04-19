from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
from src.services.project_manager_tables import Base

def get_db():
    db_conn = DbConnector()
    engine = db_conn.engine
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class DbConnector():
    initialized = False
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(DbConnector, cls).__new__(cls)
        return cls.instance
    
    def __init__(self):
        if not self.initialized:
            load_dotenv()
            SQLALCHEMY_DATABASE_URL = os.getenv("DB_CONNECTION_STRING")
            self.engine = create_engine(
                SQLALCHEMY_DATABASE_URL)
            Base.metadata.create_all(bind=self.engine)
            self.initialized = True

# napravila ovo da daje sessiju middleware-u, mokovacu ga za tesotve
def get_session():
    db_conn = DbConnector()
    return Session(bind=db_conn.engine, autocommit=False, autoflush=False)