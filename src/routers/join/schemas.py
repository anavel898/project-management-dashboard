from pydantic import BaseModel


class Invite(BaseModel):
    project_id: int
    join_token: str