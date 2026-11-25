from datetime import datetime
from typing import Optional, Literal
from zoneinfo import ZoneInfo
from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator
from utils import round_time

KYIV_TZ = ZoneInfo("Europe/Kyiv")

class CreateEvent(BaseModel):
    title: str = Field(..., examples=["Синхронізація команди"])
    description: Optional[str] = Field(None, examples=["Обговорення статусів завдань"])
    location_id: Optional[int] = Field(None, examples=[1])
    group_id: Optional[int] = Field(None, examples=[1])
    start_time: datetime = Field(
        ...,
        examples=["2026-11-20T10:00:00"],
        description="Час за Києвом (наприклад, 2026-11-20T10:00:00)"
    )
    end_time: datetime = Field(
        ...,
        examples=["2026-11-20T11:00:00"],
        description="Час за Києвом (наприклад, 2026-11-20T11:00:00)"
    )
    send_email_notification: bool = Field(False, examples=[True])

    @field_validator("start_time", "end_time", mode="after")
    @classmethod
    def clean_time(cls, value: datetime) -> datetime:
        if value.tzinfo is not None:
            value = value.replace(tzinfo=None)
        return round_time(value, step_minutes=15)

    @field_validator("end_time", mode="after")
    @classmethod
    def validate_time_range(cls, end_time: datetime, info) -> datetime:
        start_time = info.data.get("start_time")
        if start_time and end_time <= start_time:
            raise ValueError("End time cannot be before start time")
        return end_time

class UpdateEvent(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    location_id: Optional[int] = None
    start_time: Optional[datetime] = Field(
        None,
        examples=["2026-11-20T10:00:00"],
        description="Час за Києвом"
    )
    end_time: Optional[datetime] = Field(
        None,
        examples=["2026-11-20T11:00:00"],
        description="Час за Києвом"
    )

    @field_validator("start_time", "end_time", mode="after")
    @classmethod
    def clean_time(cls, value: Optional[datetime]) -> Optional[datetime]:
        if value is not None:
            if value.tzinfo is not None:
                value = value.replace(tzinfo=None)
            return round_time(value, step_minutes=15)
        return value

    @model_validator(mode="after")
    def check_dates(self):
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValueError("end_time must be after start_time")
        return self

class CreateGroup(BaseModel):
    name: str
    description: Optional[str] = None

class UpdateGroup(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class AddGroupMember(BaseModel):
    user_id: int

class LoginRequest(BaseModel):
    username: str
    password: str

class CreateLocation(BaseModel):
    office_room: str
    max_occupancy: int

class UpdateLocation(BaseModel):
    office_room: Optional[str] = None
    max_occupancy: Optional[int] = None

class CreateUser(BaseModel):
    name : str
    surname : str
    username: str
    email: EmailStr
    password: str = Field(min_length=8)

class UpdateUserRole(BaseModel):
    role: Literal["manager","employee"]

class UpdateProfile(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    surname: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = Field(None, min_length=8)

    @field_validator("name", "surname", mode="before")
    @classmethod
    def strip_whitespace(cls, v):
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("Value cannot be empty")
        return v
