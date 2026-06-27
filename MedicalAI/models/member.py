from pydantic import BaseModel

class Member(BaseModel):
    id: int
    user_id: str
    password: str

class MemberProfile(BaseModel):
    id: int
    name: str

class UserSessionDTO(BaseModel):
    id: int
    user_id: str
    name: str