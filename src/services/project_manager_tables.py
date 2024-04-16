from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy.sql import text
from src.services.database import Base

class Users(Base):
    __tablename__ = 'users'

    username = Column(String(10), primary_key=True)
    name = Column(String(50), nullable=False)
    email = Column(String(50), nullable=False)
    password = Column(String, nullable=False)

class Projects(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    created_by = Column(String(10),
                        ForeignKey('users.username'),
                        nullable=False)
    created_on = Column(DateTime, server_default=text("(datetime('now'))"))
    description = Column(String(500), nullable=False)
    updated_by = Column(String(10))
    updated_on = Column(DateTime)
    logo = Column(String(2048))

class Documents(Base):
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    project_id = Column(Integer,
                        ForeignKey('projects.id', ondelete='CASCADE'),
                        nullable=False)
    added_by = Column(String(10), ForeignKey('users.username'), nullable=False)
    link_to_document = Column(String(2048), nullable=False)

class ProjectAccess(Base):
    __tablename__ = 'project_access'

    project_id = Column(Integer,
                        ForeignKey('projects.id', ondelete='CASCADE'),
                        primary_key=True)
    username = Column(String(10),
                      ForeignKey('users.username', ondelete='CASCADE'),
                      primary_key=True)
    access_type = Column(String(10))
    is_valid = Column(Boolean, default=True)