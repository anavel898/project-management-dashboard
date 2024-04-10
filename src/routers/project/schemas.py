from pydantic import BaseModel, ConfigDict, Field


class NewProject(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(max_length=100)
    created_by: str
    description: str = Field(max_length=500)
    logo: str | None = None
    documents: list[str] | None = None
    contributors: list[int] | None = None


class ProjectData(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # updated_by will be inferred automatically when auth logic is implemented
    updated_by: str
    name: str = Field(None, max_length=100)
    created_by: str | None = None
    description: str = Field(None, max_length=500)
    logo: str | None = None
    documents: list[str] | None = None
    contributors: list[int] | None = None
