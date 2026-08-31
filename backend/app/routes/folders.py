from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.security import current_user
from app.models.models import Folder
from app.schemas.schemas import FolderCreate

router = APIRouter(prefix='/folders', tags=['folders'])

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

    f.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return {'ok': True}
