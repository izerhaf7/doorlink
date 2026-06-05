from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select

from app.database import create_db_and_tables, engine
from app.models.role_model import Role
from app.models.user_model import User  # noqa: F401 — agar SQLModel tahu tabel ini
from app.models.access_log_model import AccessLog  # noqa: F401
from app.routers import mikrotik_router, hotspot_router, user_router, access_router, esp32_router
from app.routers import dashboard_router, radius_router

app = FastAPI(
    title="DoorLink API",
    description="Backend API untuk sistem akses pintu berbasis IoT — DoorLink",
    version="0.3.0",
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Register routers
app.include_router(mikrotik_router.router)
app.include_router(hotspot_router.router)
app.include_router(user_router.router)
app.include_router(access_router.router)
app.include_router(esp32_router.router)
app.include_router(dashboard_router.router)
app.include_router(radius_router.router)


# ── Default Roles ───────────────────────────────────────────

DEFAULT_ROLES = [
    Role(name="owner", can_use_hotspot=True, can_open_door=True,
         can_use_rfid=True, can_access_dashboard=True, is_limited=False),
    Role(name="tenant", can_use_hotspot=True, can_open_door=True,
         can_use_rfid=True, can_access_dashboard=False, is_limited=False),
    Role(name="trusted_guest", can_use_hotspot=True, can_open_door=True,
         can_use_rfid=False, can_access_dashboard=False, is_limited=True),
    Role(name="guest", can_use_hotspot=True, can_open_door=False,
         can_use_rfid=False, can_access_dashboard=False, is_limited=True),
    Role(name="technician", can_use_hotspot=True, can_open_door=True,
         can_use_rfid=False, can_access_dashboard=True, is_limited=True),
]


def seed_roles():
    """Insert/update default roles agar semua role DoorLink bisa memakai HotSpot."""
    with Session(engine) as session:
        for role in DEFAULT_ROLES:
            existing = session.exec(
                select(Role).where(Role.name == role.name)
            ).first()
            if not existing:
                session.add(role)
                continue

            existing.can_use_hotspot = role.can_use_hotspot
            existing.can_open_door = role.can_open_door
            existing.can_use_rfid = role.can_use_rfid
            existing.can_access_dashboard = role.can_access_dashboard
            existing.is_limited = role.is_limited
            session.add(existing)
        session.commit()


# ── Startup Event ───────────────────────────────────────────

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    seed_roles()


# ── Root ────────────────────────────────────────────────────

@app.get("/", tags=["Root"])
def root():
    return {"message": "DoorLink Backend Running"}


@app.get("/roles", tags=["Roles"])
def get_roles():
    """Ambil daftar semua role yang tersedia."""
    with Session(engine) as session:
        return session.exec(select(Role)).all()