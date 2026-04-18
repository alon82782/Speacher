from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    name: str = Field(min_length=1, max_length=50)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isalpha() for c in v):
            raise ValueError("비밀번호에 영문자를 포함해야 합니다.")
        if not any(c.isdigit() for c in v):
            raise ValueError("비밀번호에 숫자를 포함해야 합니다.")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UpdateMeRequest(BaseModel):
    name: str = Field(min_length=1, max_length=50)


class UpdatePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=100)


class DeleteAccountRequest(BaseModel):
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    user: UserResponse
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class VerifyResponse(BaseModel):
    valid: bool
    user_id: int | None = None

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RegisterResponse(BaseModel):
    message: str
    user_id: int
    tokens: TokenPair


class LoginResponse(BaseModel):
    message: str
    tokens: TokenPair
    user: UserResponse


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str


class UpdateProfileRequest(BaseModel):
    name: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class MessageResponse(BaseModel):
    message: str

class UserProfile(BaseModel):
    id: int
    email: str
    name: str
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}