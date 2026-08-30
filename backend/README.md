# CloudDrive Backend

FastAPI API for the CloudDrive MVP. SQLite is the zero-config default; set `DATABASE_URL` to PostgreSQL for deployment. Files are stored locally by default; the storage service is intentionally isolated so S3/Supabase Storage can replace it.

## Run
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env  # Windows
# cp .env.example .env # macOS/Linux
uvicorn app.main:app --reload --port 8000
```
API docs: http://localhost:8000/docs
