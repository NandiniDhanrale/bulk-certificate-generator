from datetime import date

from pydantic import BaseModel, EmailStr, Field, field_validator


class RecipientInput(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("name must not be blank")
        return value


class JobCreate(BaseModel):
    course_name: str = Field(min_length=1, max_length=200)
    event_name: str | None = Field(default=None, max_length=200)
    completion_date: date
    recipients: list[RecipientInput]

    @field_validator("course_name")
    @classmethod
    def clean_course_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("course_name must not be blank")
        return value

    @field_validator("event_name")
    @classmethod
    def clean_event_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @field_validator("recipients")
    @classmethod
    def recipients_must_not_be_empty(
        cls, value: list[RecipientInput]
    ) -> list[RecipientInput]:
        if not value:
            raise ValueError("at least one recipient is required")
        return value


class JobCreated(BaseModel):
    id: str
    status: str
    total_count: int


class RecipientStatus(BaseModel):
    id: str
    name: str
    email: str
    status: str
    error: str | None = None
    certificate_url: str | None = None


class JobStatus(BaseModel):
    id: str
    status: str
    total_count: int
    success_count: int
    failed_count: int
    recipients: list[RecipientStatus]
