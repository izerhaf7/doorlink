from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from datetime import timedelta


def wib_now():
    return datetime.utcnow() + timedelta(hours=7)
class AccessLog(SQLModel, table=True):
    """Tabel access_logs — mencatat setiap percobaan akses pintu."""

    __tablename__ = "access_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True)
    method: str  # "web", "rfid", "hotspot"
    status: str  # "allowed", "denied"
    message: str
    created_at: datetime = Field(
    default_factory=wib_now
)



