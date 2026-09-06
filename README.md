# CloudDrive — Cloud Based Media File Storage Service

A crisp full-stack MVP inspired by Google Drive, built with FastAPI + React/Vite.

## Included

- JWT access/refresh cookies (HttpOnly)
- Email/password registration and login
- Folder hierarchy and CRUD basics
- Drag/drop and multipart uploads with progress
- Download, soft-delete, restore
- Starred view
- Viewer/editor sharing between registered users
- Public share links with optional expiry/password field
- Search and list/grid views
- Server-side authorization checks
- SlowAPI middleware
- SQLite zero-config development database, PostgreSQL-ready configuration
- Storage service with native Vercel Blob Object Storage integration (and local disk fallback)
- OpenAPI docs at `/docs`

## Quick start

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
# copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
# copy .env.example .env
npm run dev
```

Open http://localhost:5173.

## Production hardening

For production on Vercel, configure `BLOB_READ_WRITE_TOKEN` for Vercel Blob persistent object storage, set a strong `JWT_SECRET`, use PostgreSQL, enable HTTPS and secure cookies, and configure environment variables as shown in `.env.example`.
