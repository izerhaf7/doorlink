from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.database import get_session
from app.schemas.access_schema import ESP32Response
from app.services import access_service

router = APIRouter(prefix="/esp32", tags=["ESP32"])


@router.get(
    "/check-access/{username}",
    response_model=ESP32Response,
    summary="ESP32 — Cek & Log Akses Pintu",
    description=(
        "Endpoint khusus untuk simulasi ESP32 di Wokwi. "
        "Menerima username, mengecek hak akses, menyimpan log (method='esp32'), "
        "dan mengembalikan JSON ringkas yang mudah di-parse ArduinoJson."
    ),
)
def esp32_check_access(username: str, session: Session = Depends(get_session)):
    """
    Digunakan ESP32 untuk:
    1. Mengecek apakah username terdaftar, aktif, dan boleh buka pintu.
    2. Mencatat log dengan method='esp32'.
    3. Mengembalikan JSON: {username, allowed, status, message}.
    """
    return access_service.esp32_check_access(session, username)
