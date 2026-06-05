from pydantic import BaseModel, Field


class RadiusUserCreate(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class RadiusUserUpdate(BaseModel):
    password: str | None = Field(default=None, min_length=1)
    disabled: bool | None = None


class RadiusSyncRequest(BaseModel):
    delete_extra: bool = False
