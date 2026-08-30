from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware

from app.core.db import Base, engine
from app.core.config import settings
from app.routes import auth, files, folders, sharing

import os


# ---------------------------------------------------------
# DATABASE TABLES
# ---------------------------------------------------------

Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------
# STORAGE DIRECTORY
# ---------------------------------------------------------

os.makedirs(
    settings.STORAGE_DIR,
    exist_ok=True,
)


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
#
# Frontend:
# https://cloud-drive-lilac.vercel.app
#
# Backend:
# https://cloud-drive-dbpa.vercel.app
#
# We explicitly include the production frontend URL
# to prevent CORS preflight failures on Vercel.
# ---------------------------------------------------------

allowed_origins = [
    "https://cloud-drive-lilac.vercel.app",
]

# Also allow the value configured through Vercel
# environment variables, if it is different.
if settings.FRONTEND_ORIGIN:
    configured_origin = settings.FRONTEND_ORIGIN.rstrip("/")

    if configured_origin not in allowed_origins:
        allowed_origins.append(configured_origin)


# Local development support
if "http://localhost:5173" not in allowed_origins:
    allowed_origins.append("http://localhost:5173")

if "http://127.0.0.1:5173" not in allowed_origins:
    allowed_origins.append("http://127.0.0.1:5173")


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# RATE LIMITING
# ---------------------------------------------------------

app.state.limiter = Limiter(
    key_func=get_remote_address
)

app.add_middleware(
    SlowAPIMiddleware
)


# ---------------------------------------------------------
# ROUTES
# ---------------------------------------------------------

app.include_router(auth.router)
app.include_router(files.router)
app.include_router(folders.router)
app.include_router(sharing.router)


# ---------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "clouddrive-api",
    }
