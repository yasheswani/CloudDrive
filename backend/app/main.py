import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware

from app.core.db import Base, engine, SessionLocal
from app.core.config import settings
from app.core.security import hash_password
from app.models.models import User
from app.routes import auth, files, folders, sharing, activities

logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# DATABASE TABLES & STARTUP SEEDING
# ---------------------------------------------------------

Base.metadata.create_all(bind=engine)

def seed_default_users():
    try:
        db = SessionLocal()
        users_to_seed = [
            ("demo@clouddrive.com", "Demo User", "Password123!"),
            ("user2@clouddrive.com", "Second User", "Password123!"),
        ]
        for email, name, pwd in users_to_seed:
            existing = db.query(User).filter_by(email=email).first()
            if not existing:
                u = User(
                    email=email,
                    name=name,
                    password_hash=hash_password(pwd),
                )
                db.add(u)
                db.commit()
                logger.info("Seeded default user: %s", email)
        db.close()
    except Exception as e:
        logger.warning("Startup seeding skipped/failed: %s", e)

seed_default_users()

# ---------------------------------------------------------
# STORAGE DIRECTORY
# ---------------------------------------------------------

try:
    os.makedirs(settings.STORAGE_DIR, exist_ok=True)
except OSError:
    pass

# ---------------------------------------------------------
# FASTAPI APPLICATION
# ---------------------------------------------------------

app = FastAPI(
    title="CloudDrive API",
    version="1.0.0",
)

# ---------------------------------------------------------
# CORS CONFIGURATION
# ---------------------------------------------------------

allowed_origins = [
    "https://cloud-drive-lilac.vercel.app",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

if settings.FRONTEND_ORIGIN:
    configured_origin = settings.FRONTEND_ORIGIN.rstrip("/")
    if configured_origin not in allowed_origins:
        allowed_origins.append(configured_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# RATE LIMITING
# ---------------------------------------------------------

app.state.limiter = Limiter(key_func=get_remote_address)
app.add_middleware(SlowAPIMiddleware)

# ---------------------------------------------------------
# ROUTES
# ---------------------------------------------------------

app.include_router(auth.router)
app.include_router(files.router)
app.include_router(folders.router)
app.include_router(sharing.router)
app.include_router(activities.router)

# ---------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "clouddrive-api",
    }
