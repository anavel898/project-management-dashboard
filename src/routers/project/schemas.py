from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import List, Optional

class NewProject(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(max_length=100)
    description: str = Field(max_length=500)


class UpdateProject(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(None, max_length=100)
    description: str = Field(None, max_length=500)


class InviteProject(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str


class Project(BaseModel):
    id: int
    name: str
    created_by: str
    created_on: datetime
    description: str
    updated_on: Optional[datetime] = None
    updated_by: Optional[str] = None
    logo: Optional[str] = None
    documents: Optional[List[dict]] = None
    contributors: Optional[List[str]] = None


class ProjectDocument(BaseModel):
    id: int
    name: str
    added_by: str
    added_on: datetime
    project_id: int
    content_type: str


class ProjectLogo(BaseModel):
    project_id: int
    logo_name: str
    uploaded_by: str
    uploaded_on: datetime


class ProjectPermission(BaseModel):
    project_id: int
    username: str
    role: str


class CoreProjectData(BaseModel):
    id: int
    name: str
    description: str
    owner: str
    created_on: datetime


class EmailInviteProject(BaseModel):
    email: str = Field(pattern="([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+")


class SentEmailProjectInvite(BaseModel):
    aws_message_id: str
    join_token: str