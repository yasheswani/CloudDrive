import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.security import current_user
from app.models.models import Folder, File, Activity
from app.schemas.schemas import FolderCreate, FolderUpdate

router = APIRouter(prefix='/folders', tags=['folders'])

def log_act(db, user_id, action, target_type, target_id, metadata=None):
    meta = json.dumps(metadata) if metadata else None
    db.add(Activity(user_id=user_id, action=action, target_type=target_type, target_id=target_id, metadata_json=meta))

@router.get('')
def list_folders(user=Depends(current_user), db: Session = Depends(get_db)):
    folders = (
        db.query(Folder)
        .filter(Folder.owner_id == user.id, Folder.deleted_at.is_(None))
        .order_by(Folder.name)
        .all()
    )
    return [{'id': f.id, 'name': f.name, 'parent_id': f.parent_id} for f in folders]

@router.post('')
def create(data: FolderCreate, user=Depends(current_user), db: Session = Depends(get_db)):
    folder_name = data.name.strip()
    if not folder_name:
        raise HTTPException(status_code=400, detail="Folder name cannot be empty")

    if data.parent_id:
        parent = (
            db.query(Folder)
            .filter(Folder.id == data.parent_id, Folder.owner_id == user.id, Folder.deleted_at.is_(None))
            .first()
        )
        if not parent:
            raise HTTPException(status_code=404, detail="Parent folder not found")

    f = Folder(name=folder_name, owner_id=user.id, parent_id=data.parent_id)
    db.add(f)
    db.commit()
    db.refresh(f)
    log_act(db, user.id, 'create', 'folder', f.id, {'name': f.name})
    db.commit()
    return {'id': f.id, 'name': f.name, 'parent_id': f.parent_id}

@router.patch('/{id}')
def update_folder(id: int, data: FolderUpdate, user=Depends(current_user), db: Session = Depends(get_db)):
    f = (
        db.query(Folder)
        .filter(Folder.id == id, Folder.owner_id == user.id, Folder.deleted_at.is_(None))
        .first()
    )
    if not f:
        raise HTTPException(status_code=404, detail="Folder not found")

    changes = {}
    if data.name is not None and data.name.strip():
        changes['old_name'] = f.name
        f.name = data.name.strip()
        changes['new_name'] = f.name

    if data.parent_id is not None:
        if data.parent_id == f.id:
            raise HTTPException(status_code=400, detail="Folder cannot be its own parent")
        if data.parent_id != 0:
            parent = (
                db.query(Folder)
                .filter(Folder.id == data.parent_id, Folder.owner_id == user.id, Folder.deleted_at.is_(None))
                .first()
            )
            if not parent:
                raise HTTPException(status_code=404, detail="Target parent folder not found")
            f.parent_id = data.parent_id
        else:
            f.parent_id = None
        changes['parent_id'] = f.parent_id

    db.commit()
    log_act(db, user.id, 'update', 'folder', f.id, changes)
    db.commit()
    return {'id': f.id, 'name': f.name, 'parent_id': f.parent_id}

@router.delete('/{id}')
def delete(id: int, user=Depends(current_user), db: Session = Depends(get_db)):
    f = (
        db.query(Folder)
        .filter(Folder.id == id, Folder.owner_id == user.id, Folder.deleted_at.is_(None))
        .first()
    )
    if not f:
        raise HTTPException(status_code=404, detail="Folder not found")

    now_dt = datetime.now(timezone.utc)
    
    # Collect all descendant folder IDs
    folder_ids = [id]
    queue = [id]
    while queue:
        curr_id = queue.pop(0)
        children = (
            db.query(Folder.id)
            .filter(Folder.parent_id == curr_id, Folder.owner_id == user.id, Folder.deleted_at.is_(None))
            .all()
        )
        for child_id, in children:
            folder_ids.append(child_id)
            queue.append(child_id)

    db.query(Folder).filter(Folder.id.in_(folder_ids)).update({Folder.deleted_at: now_dt}, synchronize_session=False)
    db.query(File).filter(File.folder_id.in_(folder_ids), File.deleted_at.is_(None)).update({File.deleted_at: now_dt}, synchronize_session=False)
    log_act(db, user.id, 'delete', 'folder', id, {'name': f.name})
    db.commit()
    return {'ok': True}
