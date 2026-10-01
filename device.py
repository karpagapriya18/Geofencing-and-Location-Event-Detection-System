from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=6, max_length=120)


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    email: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None


class UserRead(BaseModel):
    id: int
    name: str
    email: str | None = None
    role: str = "admin"
    is_active: bool = True
    model_config = ConfigDict(from_attributes=True)


class DeviceCreate(BaseModel):
    identifier: str = Field(min_length=1, max_length=120)
    label: str | None = Field(default=None, max_length=120)
    user_id: int | None = None


class DeviceUpdate(BaseModel):
    label: str | None = Field(default=None, max_length=120)
    user_id: int | None = None
    is_active: bool | None = None


class DeviceRead(DeviceCreate):
    id: int
    is_active: bool
    model_config = ConfigDict(from_attributes=True)
