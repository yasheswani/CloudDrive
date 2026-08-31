# CloudDrive Backend

FastAPI API for the CloudDrive application. SQLite is the zero-config default; set `DATABASE_URL` to PostgreSQL for deployment. Persistent file storage uses Vercel Blob Object Storage via `BLOB_READ_WRITE_TOKEN`, with automatic fallback to local disk storage for offline local development.

## Run

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env  # Windows
# cp .env.example .env # macOS/Linux
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs
