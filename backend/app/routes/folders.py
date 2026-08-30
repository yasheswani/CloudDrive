from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.security import current_user
from app.models.models import Folder,File
from app.schemas.schemas import FolderCreate
router=APIRouter(prefix='/folders',tags=['folders'])
@router.get('')
def list_folders(user=Depends(current_user),db:Session=Depends(get_db)):
    return [{'id':f.id,'name':f.name,'parent_id':f.parent_id} for f in db.query(Folder).filter_by(owner_id=user.id,deleted_at=None).order_by(Folder.name).all()]
@router.post('')
def create(data:FolderCreate,user=Depends(current_user),db:Session=Depends(get_db)):
    if data.parent_id and not db.query(Folder).filter_by(id=data.parent_id,owner_id=user.id,deleted_at=None).first(): raise HTTPException(404,'Parent folder not found')
    f=Folder(name=data.name,owner_id=user.id,parent_id=data.parent_id); db.add(f); db.commit(); db.refresh(f); return {'id':f.id,'name':f.name,'parent_id':f.parent_id}
@router.delete('/{id}')
def delete(id:int,user=Depends(current_user),db:Session=Depends(get_db)):
    f=db.query(Folder).filter_by(id=id,owner_id=user.id,deleted_at=None).first()
    if not f: raise HTTPException(404,'Folder not found')
    from datetime import datetime,timezone
    f.deleted_at=datetime.now(timezone.utc); db.commit(); return {'ok':True}
