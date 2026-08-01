from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EarlyAccessSubmission(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    phone: str = Field(min_length=5, max_length=40)
    email: str = Field(min_length=3, max_length=255)
    lost: str = Field(pattern=r"^(Yes|No)$")
    features: list[str] = Field(default_factory=list)
    problems: list[str] = Field(default_factory=list)

    @field_validator("name", "phone", "email", mode="before")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return str(value).strip()


class EarlyAccessResponse(BaseModel):
    id: int | None = None
    name: str
    phone: str
    email: str
    lost: str
    features: list[str]
    problems: list[str]
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
