from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ChangePinRequest(BaseModel):
    current_pin: str | None = Field(default= None,min_length=4, max_length=4, pattern=r"^\d{4}$")
    new_pin: str = Field(min_length=4, max_length=4, pattern=r"^\d{4}$")

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class UpdateProfileRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone_number: str | None = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str