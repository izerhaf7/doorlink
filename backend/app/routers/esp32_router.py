from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.database import get_session
from app.models.user_model import User
from app.models.role_model import Role
from app.models.access_log_model import AccessLog
from app.services import door_command_service
from datetime import datetime
from datetime import timedelta

router = APIRouter(prefix="/esp32", tags=["ESP32"])


@router.get("/check-access/{username}")
def esp32_check_access(username: str, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == username)).first()

    if not user or not user.is_active:
        log = AccessLog(
            username=username,
            method="esp32",
            status="denied",
            message="User tidak ditemukan atau tidak aktif",
        )
        session.add(log)
        session.commit()

        return {
            "username": username,
            "allowed": False,
            "status": "denied",
            "message": "User tidak ditemukan atau tidak aktif",
        }

    role = session.exec(select(Role).where(Role.name == user.role_name)).first()

    if not role or not role.can_open_door:
        log = AccessLog(
            username=username,
            method="esp32",
            status="denied",
            message=f"Role '{user.role_name}' tidak memiliki izin buka pintu",
        )
        session.add(log)
        session.commit()

        return {
            "username": username,
            "allowed": False,
            "status": "denied",
            "message": f"Role '{user.role_name}' tidak memiliki izin buka pintu",
        }

    log = AccessLog(
        username=username,
        method="esp32",
        status="allowed",
        message="Pintu Dibuka(Lewat RFID)",
    )
    session.add(log)
    session.commit()

    return {
        "username": username,
        "allowed": True,
        "status": "allowed",
        "message": "Access granted",
    }


@router.get("/door-command")
def esp32_door_command():
    return door_command_service.consume_command()