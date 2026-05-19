from pydantic import BaseModel
from typing import Optional


class AccessCheckResponse(BaseModel):
    """Response untuk pengecekan akses pintu."""
    username: str
    allowed: bool
    reason: str


class AccessLogResponse(BaseModel):
    """Response untuk data access log."""
    id: int
    username: str
    method: str
    status: str
    message: str
    created_at: str

    class Config:
        from_attributes = True


class DoorActionResponse(BaseModel):
    """Response untuk aksi buka pintu."""
    username: str
    allowed: bool
    status: str
    message: str


class ESP32Response(BaseModel):
    """
    Response khusus ESP32 — flat JSON, mudah di-parse ArduinoJson.
    Field: username, allowed, status, message.
    """
    username: str
    allowed: bool
    status: str   # "allowed" | "denied"
    message: str  # "Access granted" | "Access denied"
