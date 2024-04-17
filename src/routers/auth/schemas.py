from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    username: str
    full_name: str
    email: str
    password: str