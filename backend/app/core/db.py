from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

from .config import settings


# =========================================================
# DATABASE URL
# =========================================================

DATABASE_URL = settings.DATABASE_URL


# =========================================================
# VALIDATE DATABASE URL
# =========================================================

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is not configured."
    )


# =========================================================
# NORMALIZE POSTGRES URL
# =========================================================

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql://",
        1,
    )


# =========================================================
# DATABASE ENGINE
# =========================================================

if DATABASE_URL.startswith("sqlite"):

    # -----------------------------------------------------
    # LOCAL DEVELOPMENT
    # -----------------------------------------------------

    engine = create_engine(
        DATABASE_URL,
        connect_args={
            "check_same_thread": False,
        },
    )

else:

    # -----------------------------------------------------
    # POSTGRESQL / VERCEL
    # -----------------------------------------------------

    engine = create_engine(
        DATABASE_URL,
        poolclass=NullPool,
        pool_pre_ping=True,
    )


# =========================================================
# DATABASE SESSION
# =========================================================

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


# =========================================================
# BASE MODEL
# =========================================================

Base = declarative_base()


# =========================================================
# DATABASE DEPENDENCY
# =========================================================

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
