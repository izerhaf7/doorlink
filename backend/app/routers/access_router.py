from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.database import get_session
from app.schemas.access_schema import AccessCheckResponse, AccessLogResponse, DoorActionResponse
from app.services import access_service

router = APIRouter(prefix="/access", tags=["Access Control"])


@router.get("/check-door/{username}", response_model=AccessCheckResponse)
def check_door(username: str, session: Session = Depends(get_session)):
    """Cek apakah user diizinkan membuka pintu."""
    return access_service.check_door_access(session, username)


@router.post("/open-door/{username}", response_model=DoorActionResponse)
def open_door(username: str, session: Session = Depends(get_session)):
    """
    Simulasi buka pintu.
    Mencatat access log dengan status allowed/denied.
    """
    return access_service.open_door(session, username)


@router.get("/logs")
def get_logs(session: Session = Depends(get_session)):
    """Ambil seluruh access log, urut dari yang terbaru."""
    logs = access_service.get_access_logs(session)
    return [
        AccessLogResponse(
            id=log.id,
            username=log.username,
            method=log.method,
            status=log.status,
            message=log.message,
            created_at=str(log.created_at),
        )
        for log in logs
    ]

