from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class OrganisationRegisterRequest(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=200,
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128,
    )


class OrganisationResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    is_verified: bool
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )

class OrganisationLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=128,
    )


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int