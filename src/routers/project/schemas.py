from pydantic import BaseModel, ConfigDict, Field


class NewProject(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(max_length=100)
    ownerId: int
    description: str = Field(max_length=500)
    logo: str | None = None
    documents: str | None = None
    contributors: list[int] | None = None


class ProjectData(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(None, max_length=100)
    ownerId: int | None = None
    description: str = Field(None, max_length=500)
    logo: str | None = None
    documents: str | None = None
    contributors: list[int] | None = None
