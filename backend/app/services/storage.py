import os, uuid
from pathlib import Path
from fastapi import UploadFile
from app.core.config import settings

root=Path(settings.STORAGE_DIR); root.mkdir(parents=True,exist_ok=True)
async def save_upload(upload:UploadFile):
    key=f"{uuid.uuid4().hex}_{Path(upload.filename or 'file').name}"
    dest=root/key; size=0
    with dest.open('wb') as f:
        while chunk:=await upload.read(1024*1024): f.write(chunk); size+=len(chunk)
    return key,size
def path(key): return root/key
def remove(key):
    p=path(key)
    if p.exists(): p.unlink()
