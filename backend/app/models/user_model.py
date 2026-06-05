from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from datetime import timedelta


def wib_now():
    return datetime.utcnow() + timedelta(hours=7)
class User(SQLModel, table=True):
    """Tabel users — data user lokal DoorLink."""

    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    full_name: str
    username: str = Field(unique=True, index=True)
    password: str
    role_name: str = Field(index=True)
    room_number: Optional[str] = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(
    default_factory=wib_now
)

