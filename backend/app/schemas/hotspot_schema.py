from pydantic import BaseModel
from typing import Optional


class HotspotUserCreate(BaseModel):
    """Schema untuk membuat user hotspot baru."""
    name: str
    password: str
    profile: Optional[str] = "default"
