from sqlmodel import SQLModel, Field
from typing import Optional


class Role(SQLModel, table=True):
    """Tabel roles — mendefinisikan hak akses setiap role di DoorLink."""

    __tablename__ = "roles"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    can_use_hotspot: bool = Field(default=False)
    can_open_door: bool = Field(default=False)
    can_use_rfid: bool = Field(default=False)
    can_access_dashboard: bool = Field(default=False)
    is_limited: bool = Field(default=True)
