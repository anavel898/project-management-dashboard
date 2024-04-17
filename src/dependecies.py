from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
from src.services.project_manager_tables import Base

#Base.metadata.create_all(bind=engine)
#Base = declarative_base()
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
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(DbConnector, cls).__new__(cls)
        return cls.instance
    
    def __init__(self):    
        load_dotenv()
        SQLALCHEMY_DATABASE_URL = os.getenv("DB_CONNECTION_STRING")

        self.engine = create_engine(
            SQLALCHEMY_DATABASE_URL)
        
        Base.metadata.create_all(bind=self.engine)
