from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select, func

from app.database import get_session
from app.models.user_model import User
from app.models.role_model import Role
from app.models.access_log_model import AccessLog
from app.services import user_service, access_service
from app.services.mikrotik_service import mikrotik_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
templates = Jinja2Templates(directory="app/templates")


# ── GET /dashboard ──────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
def dashboard_home(request: Request, session: Session = Depends(get_session)):
    """Halaman utama dashboard — ringkasan statistik."""

    user_count = session.exec(select(func.count()).select_from(User)).one()
    role_count = session.exec(select(func.count()).select_from(Role)).one()
    log_count = session.exec(select(func.count()).select_from(AccessLog)).one()

    # Hotspot active — tangani jika MikroTik offline
    hotspot_active_count = 0
    mikrotik_online = False
    try:
        active_list = mikrotik_service.get_hotspot_active()
        hotspot_active_count = len(active_list)
        mikrotik_online = True
    except Exception:
        mikrotik_online = False

    # 5 log terbaru
    recent_logs = session.exec(
        select(AccessLog).order_by(AccessLog.created_at.desc()).limit(5)
    ).all()

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "page": "home",
            "user_count": user_count,
            "role_count": role_count,
            "log_count": log_count,
            "hotspot_active_count": hotspot_active_count,
            "mikrotik_online": mikrotik_online,
            "recent_logs": recent_logs,
        },
    )


# ── GET /dashboard/users ───────────────────────────────────

@router.get("/users", response_class=HTMLResponse)
def dashboard_users(request: Request, session: Session = Depends(get_session)):
    """Halaman manajemen user."""
    users = user_service.get_all_users(session)
    roles = session.exec(select(Role)).all()
    return templates.TemplateResponse(
        request=request,
        name="users.html",
        context={"page": "users", "users": users, "roles": roles},
    )


# ── POST /dashboard/users ──────────────────────────────────

@router.post("/users", response_class=HTMLResponse)
def dashboard_create_user(
    request: Request,
    full_name: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    role_name: str = Form(...),
    room_number: str = Form(None),
    session: Session = Depends(get_session),
):
    """Buat user baru via form dashboard."""
    error = None
    try:
        user_service.create_user(
            session=session,
            full_name=full_name,
            username=username,
            password=password,
            role_name=role_name,
            room_number=room_number or None,
        )
    except Exception as e:
        error = str(e.detail) if hasattr(e, "detail") else str(e)

    # Reload data
    users = user_service.get_all_users(session)
    roles = session.exec(select(Role)).all()

    return templates.TemplateResponse(
        request=request,
        name="users.html",
        context={
            "page": "users",
            "users": users,
            "roles": roles,
            "error": error,
            "success": "User berhasil ditambahkan!" if not error else None,
        },
    )


# ── POST /dashboard/users/{username}/delete ─────────────────

@router.post("/users/{username}/delete", response_class=HTMLResponse)
def dashboard_delete_user(
    username: str,
    session: Session = Depends(get_session),
):
    """Hapus user via dashboard."""
    try:
        user_service.delete_user(session, username)
    except Exception:
        pass
    return RedirectResponse(url="/dashboard/users", status_code=303)


# ── GET /dashboard/logs ─────────────────────────────────────

@router.get("/logs", response_class=HTMLResponse)
def dashboard_logs(request: Request, session: Session = Depends(get_session)):
    """Halaman access log."""
    logs = access_service.get_access_logs(session)
    return templates.TemplateResponse(
        request=request,
        name="logs.html",
        context={"page": "logs", "logs": logs},
    )


# ── GET /dashboard/door ─────────────────────────────────────

@router.get("/door", response_class=HTMLResponse)
def dashboard_door(request: Request):
    """Halaman simulasi akses pintu."""
    return templates.TemplateResponse(
        request=request,
        name="door.html",
        context={"page": "door", "result": None},
    )


# ── POST /dashboard/door/check ──────────────────────────────

@router.post("/door/check", response_class=HTMLResponse)
def dashboard_door_check(
    request: Request,
    username: str = Form(...),
    session: Session = Depends(get_session),
):
    """Cek akses pintu dari dashboard."""
    result = access_service.check_door_access(session, username)
    result["action"] = "check"
    return templates.TemplateResponse(
        request=request,
        name="door.html",
        context={"page": "door", "result": result, "form_username": username},
    )


# ── POST /dashboard/door/open ───────────────────────────────

@router.post("/door/open", response_class=HTMLResponse)
def dashboard_door_open(
    request: Request,
    username: str = Form(...),
    session: Session = Depends(get_session),
):
    """Simulasi buka pintu dari dashboard."""
    result = access_service.open_door(session, username)
    result["action"] = "open"
    return templates.TemplateResponse(
        request=request,
        name="door.html",
        context={"page": "door", "result": result, "form_username": username},
    )
