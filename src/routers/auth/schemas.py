from pydantic import BaseModel
from fastapi import Form


class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    username: str
    full_name: str
    email: str
    password: str

    @classmethod
    def as_form(cls,
                username: str = Form(),
                full_name: str = Form(),
                email: str = Form(pattern="([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+"),
                password: str = Form()):
        return cls(username=username, full_name=full_name, email=email, password=password)
        