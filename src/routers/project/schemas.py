from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import List, Optional

class NewProject(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(max_length=100)
    # created_by will be inferred automatically when auth logic is implemented
    created_by: str
    description: str = Field(max_length=500)


class UpdateProject(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # updated_by will be inferred automatically when auth logic is implemented
    updated_by: str
    name: str = Field(None, max_length=100)
    description: str = Field(None, max_length=500)


class Project(BaseModel):
    id: int
    name: str
    created_by: str
    created_on: datetime
    description: str
    updated_on: Optional[datetime] = None
    updated_by: Optional[str] = None
    logo: Optional[str] = None
    documents: Optional[List[dict[int, str]]] = None
    contributors: Optional[List[str]] = None
