import secrets
from datetime import datetime,timezone
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
from app.core.db import get_db
from app.core.security import current_user,hash_password
from app.models.models import File,Share,LinkShare,User
from app.schemas.schemas import ShareCreate,LinkCreate
from app.services.storage import path
router=APIRouter(tags=['sharing'])
@router.post('/shares')
def share(data:ShareCreate,user=Depends(current_user),db:Session=Depends(get_db)):
    f=db.query(File).filter_by(id=data.file_id,owner_id=user.id,deleted_at=None).first()
    target=db.query(User).filter_by(email=data.email.lower()).first()
    if not f or not target: raise HTTPException(404,'File or user not found')
    if target.id==user.id: raise HTTPException(400,'You already own this file')
    s=db.query(Share).filter_by(file_id=f.id,user_id=target.id).first()
    if s: s.role=data.role
    else: db.add(Share(file_id=f.id,user_id=target.id,role=data.role))
    db.commit(); return {'ok':True,'email':target.email,'role':data.role}
@router.post('/public-link')
def public_link(data:LinkCreate,user=Depends(current_user),db:Session=Depends(get_db)):
    f=db.query(File).filter_by(id=data.file_id,owner_id=user.id,deleted_at=None).first()
    if not f: raise HTTPException(404,'File not found')
    l=LinkShare(file_id=f.id,token=secrets.token_urlsafe(32),expires_at=data.expires_at,password_hash=hash_password(data.password) if data.password else None); db.add(l); db.commit(); db.refresh(l); return {'token':l.token,'expires_at':l.expires_at}
@router.get('/public/{token}')
def public_file(token:str,db:Session=Depends(get_db)):
    l=db.query(LinkShare).filter_by(token=token).first()
    if not l or (l.expires_at and l.expires_at < datetime.now(timezone.utc)): raise HTTPException(404,'Link expired or invalid')
    f=db.get(File,l.file_id)
    return FileResponse(path(f.storage_key),filename=f.name,media_type=f.mime_type)
