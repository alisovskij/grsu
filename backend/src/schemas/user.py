from pydantic import BaseModel


class UserSchema(BaseModel):
    id: int
    username: str
    email: str
    password: str
    role: str
    post: str
    schedule_id: str

    class Config:
        from_attributes = True


class UserLoginSchema(BaseModel):
    email: str
    password: str


class UserRegisterSchema(UserLoginSchema):
    username: str