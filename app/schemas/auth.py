from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str