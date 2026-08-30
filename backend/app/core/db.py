from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

from .config import settings


DATABASE_URL = settings.DATABASE_URL


# Supabase may provide postgres://
# SQLAlchemy expects postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql://",
        1,
    )


# ---------------------------------------------------------
# Database engine
# ---------------------------------------------------------

if DATABASE_URL.startswith("sqlite"):
    # Local development
    connect_args = {
        "check_same_thread": False
    }

    engine = create_engine(
        DATABASE_URL,
        connect_args=connect_args,
    )

else:
    # Supabase PostgreSQL / Vercel
    # NullPool is recommended for serverless deployments.
    engine = create_engine(
        DATABASE_URL,
        poolclass=NullPool,
        pool_pre_ping=True,
    )


# ---------------------------------------------------------
# Session
# ---------------------------------------------------------

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


# ---------------------------------------------------------
# Base model
# ---------------------------------------------------------

Base = declarative_base()


# ---------------------------------------------------------
# Database dependency
# ---------------------------------------------------------

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
