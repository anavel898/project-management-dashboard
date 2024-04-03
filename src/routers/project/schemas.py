from pydantic import BaseModel, ConfigDict, Field


class NewProject(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(max_length=100)
    createdBy: int
    description: str = Field(max_length=500)
    logo: str | None = None
    documents: str | None = None
    contributors: list[int] | None = None


class ProjectData(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # updatedBy will be inferred automatically when auth logic is implemented
    updatedBy: int
    name: str = Field(None, max_length=100)
    createdBy: int | None = None
    description: str = Field(None, max_length=500)
    logo: str | None = None
    documents: str | None = None
    contributors: list[int] | None = None
