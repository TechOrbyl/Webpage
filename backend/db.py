from collections.abc import Generator
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from .config import settings


class Base(DeclarativeBase):
    pass


class EarlyAccessEntry(Base):
    __tablename__ = "early_access_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    phone: Mapped[str] = mapped_column(String(40), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    lost_invoices_or_warranty: Mapped[str] = mapped_column(String(20), nullable=False)
    features: Mapped[str] = mapped_column(Text, default="")
    ownership_problems: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


_engine = None
SessionLocal = None
if settings.database_url and "USER:PASSWORD" not in settings.database_url:
    database_url = settings.database_url
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    _engine = create_engine(database_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)


def init_db() -> bool:
    if _engine is None:
        return False
    try:
        Base.metadata.create_all(_engine)
        return True
    except Exception:
        return False


def get_db() -> Generator:
    if SessionLocal is None:
        yield None
        return
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
