from sqlmodel import SQLModel, Session, create_engine
from app.config import DATABASE_URL

# SQLite needs check_same_thread=False untuk FastAPI
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)


def create_db_and_tables():
    """Buat semua tabel yang didefinisikan oleh SQLModel."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Dependency untuk mendapatkan database session."""
    with Session(engine) as session:
        yield session
