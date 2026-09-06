import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, UploadFile, File as Upload, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
import httpx
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.security import current_user
from app.models.models import File, Folder, Share, Star, Activity
from app.schemas.schemas import FileUpdate
from app.services.storage import save_upload, get_file_target, get_storage_response, remove

router = APIRouter(prefix='/files', tags=['files'])

def access(db, user, f):
    if f.owner_id == user.id:
        return 'owner'
    s = db.query(Share).filter_by(file_id=f.id, user_id=user.id).first()
    return s.role if s else None

def log_act(db, user_id, action, target_type, target_id, metadata=None):
    meta = json.dumps(metadata) if metadata else None
    db.add(Activity(user_id=user_id, action=action, target_type=target_type, target_id=target_id, metadata_json=meta))

@router.get('')
def list_files(q: str = '', folder_id: int | None = None, view: str = 'drive', user = Depends(current_user), db: Session = Depends(get_db)):
    if view == 'trash':
        fs = db.query(File).filter(File.owner_id == user.id, File.deleted_at.is_not(None)).all()
    elif view == 'shared':
        fs = db.query(File).join(Share, Share.file_id == File.id).filter(Share.user_id == user.id, File.deleted_at.is_(None)).all()
    elif view == 'starred':
        fs = db.query(File).join(Star, Star.file_id == File.id).filter(Star.user_id == user.id, File.deleted_at.is_(None)).all()
    else:
        fs = db.query(File).filter(File.owner_id == user.id, File.deleted_at.is_(None), File.folder_id == folder_id if folder_id is not None else File.folder_id.is_(None)).all()
    if q:
        fs = [f for f in fs if q.lower() in f.name.lower()]
    return [{'id': f.id, 'name': f.name, 'size': f.size, 'mime_type': f.mime_type, 'folder_id': f.folder_id, 'starred': f.starred, 'deleted_at': f.deleted_at.isoformat() if f.deleted_at else None, 'updated_at': f.updated_at.isoformat() if f.updated_at else None} for f in fs]

@router.post('/upload')
async def upload(file: UploadFile = Upload(...), folder_id: int | None = Query(None), user = Depends(current_user), db: Session = Depends(get_db)):
    if folder_id and not db.query(Folder).filter_by(id=folder_id, owner_id=user.id, deleted_at=None).first():
        raise HTTPException(404, 'Folder not found')
    key, size = await save_upload(file)
    f = File(
        name=file.filename or 'Untitled',
        owner_id=user.id,
        folder_id=folder_id,
        storage_key=key,
        size=size,
        mime_type=file.content_type or 'application/octet-stream'
    )
    db.add(f)
    db.commit()
    db.refresh(f)
    log_act(db, user.id, 'upload', 'file', f.id, {'name': f.name, 'size': f.size})
    db.commit()
    return {'id': f.id, 'name': f.name, 'size': size, 'mime_type': f.mime_type, 'folder_id': f.folder_id}

@router.get('/{id}/download')
async def download(id: int, user = Depends(current_user), db: Session = Depends(get_db)):
    f = db.get(File, id)
    role = access(db, user, f) if f else None
    if not f or not role or f.deleted_at:
        raise HTTPException(404, 'File not found')
    return await get_storage_response(f.storage_key, filename=f.name, mime_type=f.mime_type, inline=False)

@router.get('/{id}/preview')
async def preview(id: int, user = Depends(current_user), db: Session = Depends(get_db)):
    f = db.get(File, id)
    role = access(db, user, f) if f else None
    if not f or not role or f.deleted_at:
        raise HTTPException(404, 'File not found')
    return await get_storage_response(f.storage_key, filename=f.name, mime_type=f.mime_type, inline=True)

@router.patch('/{id}')
def update_file(id: int, data: FileUpdate, user = Depends(current_user), db: Session = Depends(get_db)):
    f = db.get(File, id)
    if not f or access(db, user, f) not in ('owner', 'editor') or f.deleted_at:
        raise HTTPException(404, 'File not found or forbidden')
    
    changes = {}
    if data.name is not None and data.name.strip():
        changes['old_name'] = f.name
        f.name = data.name.strip()
        changes['new_name'] = f.name
    
    if data.folder_id is not None:
        if data.folder_id != 0:
            target_folder = db.query(Folder).filter_by(id=data.folder_id, owner_id=user.id, deleted_at=None).first()
            if not target_folder:
                raise HTTPException(404, 'Target folder not found')
            f.folder_id = data.folder_id
        else:
            f.folder_id = None
        changes['folder_id'] = f.folder_id
    
    db.commit()
    log_act(db, user.id, 'update', 'file', f.id, changes)
    db.commit()
    return {'id': f.id, 'name': f.name, 'folder_id': f.folder_id}

@router.delete('/{id}')
def trash(id: int, permanent: bool = Query(False), user = Depends(current_user), db: Session = Depends(get_db)):
    f = db.get(File, id)
    if not f or access(db, user, f) not in ('owner', 'editor'):
        raise HTTPException(404, 'File not found or forbidden')
    if permanent or f.deleted_at is not None:
        remove(f.storage_key)
        db.delete(f)
        log_act(db, user.id, 'delete_permanent', 'file', id, {'name': f.name})
        db.commit()
        return {'ok': True, 'deleted': True}
    f.deleted_at = datetime.now(timezone.utc)
    log_act(db, user.id, 'trash', 'file', f.id, {'name': f.name})
    db.commit()
    return {'ok': True}

@router.post('/{id}/restore')
def restore(id: int, user = Depends(current_user), db: Session = Depends(get_db)):
    f = db.query(File).filter_by(id=id, owner_id=user.id).first()
    if not f:
        raise HTTPException(404, 'File not found')
    f.deleted_at = None
    log_act(db, user.id, 'restore', 'file', f.id, {'name': f.name})
    db.commit()
    return {'ok': True}

@router.post('/{id}/star')
def star(id: int, user = Depends(current_user), db: Session = Depends(get_db)):
    f = db.query(File).filter_by(id=id, owner_id=user.id).first()
    if not f:
        raise HTTPException(404, 'File not found')
    existing = db.query(Star).filter_by(file_id=id, user_id=user.id).first()
    if existing:
        db.delete(existing)
        f.starred = False
        action = 'unstar'
    else:
        db.add(Star(file_id=id, user_id=user.id))
        f.starred = True
        action = 'star'
    log_act(db, user.id, action, 'file', f.id, {'name': f.name})
    db.commit()
    return {'starred': f.starred}
