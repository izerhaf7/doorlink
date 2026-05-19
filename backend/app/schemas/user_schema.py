from pydantic import BaseModel
from typing import Optional


class UserCreate(BaseModel):
    """Schema untuk membuat user DoorLink baru."""
    full_name: str
    username: str
    password: str
    role_name: str
    room_number: Optional[str] = None


class UserResponse(BaseModel):
    """Schema response data user (tanpa password)."""
    id: int
    full_name: str
    username: str
    role_name: str
    room_number: Optional[str] = None
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True
