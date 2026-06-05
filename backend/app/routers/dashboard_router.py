from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select, func, delete

from app.database import get_session
from app.models.user_model import User
from app.models.role_model import Role
from app.models.access_log_model import AccessLog

from app.services import user_service, access_service
from app.services import door_command_service
from app.services.mikrotik_service import mikrotik_service

from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from datetime import datetime, timedelta
from io import StringIO, BytesIO
import csv
from openpyxl import Workbook


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
templates = Jinja2Templates(directory="app/templates")


def get_logged_user(request: Request, session: Session) -> User | None:
    username = request.cookies.get("doorlink_user")

    if not username:
        return None

    return session.exec(
        select(User).where(User.username == username)
    ).first()


def require_owner(request: Request, session: Session) -> User | RedirectResponse:
    user = get_logged_user(request, session)

    if not user or user.role_name != "owner":
        return RedirectResponse(url="/dashboard/doorlink", status_code=303)

    return user


@router.get("/", response_class=HTMLResponse)
def dashboard_root():
    return RedirectResponse(url="/dashboard/doorlink", status_code=303)


# ── LOGIN PAGE ─────────────────────────────────────────────

@router.get("/doorlink", response_class=HTMLResponse)
def doorlink_login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="doorlink_login.html",
        context={"error": None},
    )


@router.post("/doorlink", response_class=HTMLResponse)
def doorlink_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session),
):
    user = session.exec(
        select(User).where(User.username == username)
    ).first()

    if not user or user.password != password or not user.is_active:
        return templates.TemplateResponse(
            request=request,
            name="doorlink_login.html",
            context={"error": "Username atau password salah"},
        )

    if user.role_name == "owner":
        response = RedirectResponse(
            url="/dashboard/doorlink/admin",
            status_code=303,
        )
    else:
        response = RedirectResponse(
            url="/dashboard/doorlink/guest",
            status_code=303,
        )

    response.set_cookie(
        key="doorlink_user",
        value=user.username,
        httponly=True,
        max_age=60 * 60 * 6,
    )

    return response


@router.get("/doorlink/logout")
def doorlink_logout():
    response = RedirectResponse(
        url="/dashboard/doorlink",
        status_code=303,
    )

    response.delete_cookie("doorlink_user")
    return response


# ── GUEST DASHBOARD ────────────────────────────────────────

@router.get("/doorlink/guest", response_class=HTMLResponse)
def doorlink_guest(
    request: Request,
    session: Session = Depends(get_session),
):
    user = get_logged_user(request, session)

    if not user:
        return RedirectResponse(url="/dashboard/doorlink", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="doorlink_guest.html",
        context={
            "page": "doorlink_guest",
            "result": None,
            "form_username": user.username,
            "logged_user": user,
            "guest_mode": True,
        },
    )


@router.post("/doorlink/guest/open", response_class=HTMLResponse)
def doorlink_guest_open(
    request: Request,
    session: Session = Depends(get_session),
):
    user = get_logged_user(request, session)

    if not user:
        return RedirectResponse(url="/dashboard/doorlink", status_code=303)

    result = access_service.open_door(session, user.username)
    result["action"] = "open"

    if result.get("status") == "allowed":
        door_command_service.trigger_open(source=user.username)

    return templates.TemplateResponse(
        request=request,
        name="doorlink_guest.html",
        context={
            "page": "doorlink_guest",
            "result": result,
            "form_username": user.username,
            "logged_user": user,
            "guest_mode": True,
        },
    )


# ── ADMIN DASHBOARD ────────────────────────────────────────

@router.get("/doorlink/admin", response_class=HTMLResponse)
def dashboard_admin(
    request: Request,
    session: Session = Depends(get_session),
):
    user = get_logged_user(request, session)

    if not user or user.role_name != "owner":
        return RedirectResponse(url="/dashboard/doorlink", status_code=303)

    user_count = session.exec(
        select(func.count()).select_from(User)
    ).one()

    role_count = session.exec(
        select(func.count()).select_from(Role)
    ).one()

    log_count = session.exec(
        select(func.count()).select_from(AccessLog)
    ).one()

    hotspot_active_count = 0
    mikrotik_online = False

    try:
        active_list = mikrotik_service.get_hotspot_active()
        hotspot_active_count = len(active_list)
        mikrotik_online = True
    except Exception:
        mikrotik_online = False

    recent_logs = session.exec(
        select(AccessLog)
        .order_by(AccessLog.created_at.desc())
        .limit(5)
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
            "logged_user": user,
        },
    )


@router.get("/doorlink/admin/users", response_class=HTMLResponse)
def dashboard_users(
    request: Request,
    session: Session = Depends(get_session),
):
    user = get_logged_user(request, session)

    if not user or user.role_name != "owner":
        return RedirectResponse(url="/dashboard/doorlink", status_code=303)

    users = user_service.get_all_users(session)
    roles = session.exec(select(Role)).all()

    return templates.TemplateResponse(
        request=request,
        name="users.html",
        context={
            "page": "users",
            "users": users,
            "roles": roles,
            "logged_user": user,
        },
    )


@router.post("/doorlink/admin/users", response_class=HTMLResponse)
def dashboard_create_user(
    request: Request,
    full_name: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    role_name: str = Form(...),
    room_number: str = Form(None),
    session: Session = Depends(get_session),
):
    user = get_logged_user(request, session)

    if not user or user.role_name != "owner":
        return RedirectResponse(url="/dashboard/doorlink", status_code=303)

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
            "logged_user": user,
        },
    )

@router.post("/doorlink/admin/users/{username}/update", response_class=HTMLResponse)
def dashboard_update_user(
    request: Request,
    username: str,
    full_name: str = Form(...),
    role_name: str = Form(...),
    room_number: str = Form(None),
    session: Session = Depends(get_session),
):
    user = get_logged_user(request, session)

    if not user or user.role_name != "owner":
        return RedirectResponse(url="/dashboard/doorlink", status_code=303)

    target_user = session.exec(
        select(User).where(User.username == username)
    ).first()

    if target_user:
        target_user.full_name = full_name
        target_user.role_name = role_name
        target_user.room_number = room_number or None

        session.add(target_user)
        session.commit()

    return RedirectResponse(
        url="/dashboard/doorlink/admin/users",
        status_code=303,
    )

@router.post("/doorlink/admin/users/{username}/delete", response_class=HTMLResponse)
def dashboard_delete_user(
    request: Request,
    username: str,
    session: Session = Depends(get_session),
):
    user = get_logged_user(request, session)

    if not user or user.role_name != "owner":
        return RedirectResponse(url="/dashboard/doorlink", status_code=303)

    try:
        user_service.delete_user(session, username)
    except Exception:
        pass

    return RedirectResponse(
        url="/dashboard/doorlink/admin/users",
        status_code=303,
    )


@router.get("/doorlink/admin/logs", response_class=HTMLResponse)
def dashboard_logs(
    request: Request,
    session: Session = Depends(get_session),
):
    user = get_logged_user(request, session)

    if not user or user.role_name != "owner":
        return RedirectResponse(url="/dashboard/doorlink", status_code=303)

    logs = access_service.get_access_logs(session)

    return templates.TemplateResponse(
        request=request,
        name="logs.html",
        context={
            "page": "logs",
            "logs": logs,
            "logged_user": user,
        },
    )


@router.post("/doorlink/admin/logs/clear")
def dashboard_clear_logs(
    request: Request,
    session: Session = Depends(get_session),
):
    user = get_logged_user(request, session)

    if not user or user.role_name != "owner":
        return RedirectResponse(url="/dashboard/doorlink", status_code=303)

    session.exec(delete(AccessLog))
    session.commit()

    return RedirectResponse(
        url="/dashboard/doorlink/admin/logs",
        status_code=303,
    )

@router.post("/doorlink/admin/logs/clear/{days}")
def dashboard_clear_logs_older_than(
    request: Request,
    days: int,
    session: Session = Depends(get_session),
):
    user = get_logged_user(request, session)

    if not user or user.role_name != "owner":
        return RedirectResponse(url="/dashboard/doorlink", status_code=303)

    cutoff_date = datetime.now() - timedelta(days=days)

    old_logs = session.exec(
        select(AccessLog).where(AccessLog.created_at < cutoff_date)
    ).all()

    for log in old_logs:
        session.delete(log)

    session.commit()

    return RedirectResponse(
        url="/dashboard/doorlink/admin/logs",
        status_code=303,
    )


@router.get("/doorlink/admin/logs/export/csv")
def dashboard_export_logs_csv(
    request: Request,
    session: Session = Depends(get_session),
):
    user = get_logged_user(request, session)

    if not user or user.role_name != "owner":
        return RedirectResponse(url="/dashboard/doorlink", status_code=303)

    logs = session.exec(
        select(AccessLog).order_by(AccessLog.created_at.desc())
    ).all()

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(["Waktu", "Username", "Method", "Status", "Message"])

    for log in logs:
        writer.writerow([
            log.created_at.strftime("%d %b %Y %H:%M:%S") if log.created_at else "-",
            log.username,
            log.method,
            log.status,
            log.message,
        ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=doorlink_access_logs.csv"
        },
    )


@router.get("/doorlink/admin/logs/export/excel")
def dashboard_export_logs_excel(
    request: Request,
    session: Session = Depends(get_session),
):
    user = get_logged_user(request, session)

    if not user or user.role_name != "owner":
        return RedirectResponse(url="/dashboard/doorlink", status_code=303)

    logs = session.exec(
        select(AccessLog).order_by(AccessLog.created_at.desc())
    ).all()

    wb = Workbook()
    ws = wb.active
    ws.title = "Access Logs"

    ws.append(["Waktu", "Username", "Method", "Status", "Message"])

    for log in logs:
        ws.append([
            log.created_at.strftime("%d %b %Y %H:%M:%S") if log.created_at else "-",
            log.username,
            log.method,
            log.status,
            log.message,
        ])

    file_stream = BytesIO()
    wb.save(file_stream)
    file_stream.seek(0)

    return StreamingResponse(
        file_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=doorlink_access_logs.xlsx"
        },
    )


@router.get("/doorlink/admin/door", response_class=HTMLResponse)
def dashboard_admin_door(
    request: Request,
    session: Session = Depends(get_session),
):
    user = get_logged_user(request, session)

    if not user or user.role_name != "owner":
        return RedirectResponse(url="/dashboard/doorlink", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="door.html",
        context={
            "page": "door",
            "result": None,
            "form_username": "",
            "logged_user": user,
            "guest_mode": False,
        },
    )


@router.post("/doorlink/admin/door/open", response_class=HTMLResponse)
def dashboard_admin_door_open(
    request: Request,
    username: str = Form(...),
    session: Session = Depends(get_session),
):
    user = get_logged_user(request, session)

    if not user or user.role_name != "owner":
        return RedirectResponse(url="/dashboard/doorlink", status_code=303)

    result = access_service.open_door(session, username)
    result["action"] = "open"

    if result.get("status") == "allowed":
        door_command_service.trigger_open(source=username)

    return templates.TemplateResponse(
        request=request,
        name="door.html",
        context={
            "page": "door",
            "result": result,
            "form_username": username,
            "logged_user": user,
            "guest_mode": False,
        },
    )

@router.post("/doorlink/admin/users/{username}/update", response_class=HTMLResponse)
def dashboard_update_user(
    request: Request,
    username: str,
    full_name: str = Form(...),
    role_name: str = Form(...),
    room_number: str = Form(None),
    session: Session = Depends(get_session),
):
    user = get_logged_user(request, session)

    if not user or user.role_name != "owner":
        return RedirectResponse(url="/dashboard/doorlink", status_code=303)

    target_user = session.exec(
        select(User).where(User.username == username)
    ).first()

    if target_user:
        target_user.full_name = full_name
        target_user.role_name = role_name
        target_user.room_number = room_number or None

        session.add(target_user)
        session.commit()

    return RedirectResponse(
        url="/dashboard/doorlink/admin/users",
        status_code=303,
    )