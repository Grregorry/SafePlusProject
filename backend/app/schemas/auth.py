from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)


OrganisationCategory = Literal[
    "Construction",
    "Mining and quarrying",
    "Manufacturing",
    "Healthcare",
    "Transport and logistics",
    "Agriculture",
    "Retail",
    "Hospitality",
    "Professional services",
    "Other",
]


class OrganisationRegisterRequest(
    BaseModel
):
    name: str = Field(
        min_length=2,
        max_length=200,
    )

    category: OrganisationCategory

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128,
    )

    @field_validator("name")
    @classmethod
    def clean_name(
        cls,
        value: str,
    ) -> str:
        cleaned_name = " ".join(
            value.split()
        )

        if len(cleaned_name) < 2:
            raise ValueError(
                (
                    "Organisation name must "
                    "contain at least two "
                    "characters."
                )
            )

        return cleaned_name


class OrganisationResponse(BaseModel):
    id: int
    name: str
    category: OrganisationCategory
    email: EmailStr
    is_verified: bool
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class OrganisationLoginRequest(
    BaseModel
):
    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128,
    )


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int