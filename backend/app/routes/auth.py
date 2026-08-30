from fastapi import APIRouter,Depends,Response,HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.security import hash_password,verify_password,token,current_user
from app.models.models import User
from app.schemas.schemas import Register,Login
router=APIRouter(prefix='/auth',tags=['auth'])
def set_tokens(response, user):
    response.set_cookie(
        key="access_token",
        value=token(str(user.id), minutes=30),
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
    )

    response.set_cookie(
        key="refresh_token",
        value=token(str(user.id), days=14),
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
    )
@router.post('/register')
def register(data:Register,response:Response,db:Session=Depends(get_db)):
    if db.query(User).filter_by(email=data.email.lower()).first(): raise HTTPException(409,'Email already registered')
    u=User(email=data.email.lower(),name=data.name,password_hash=hash_password(data.password)); db.add(u); db.commit(); db.refresh(u); set_tokens(response,u); return {'id':u.id,'email':u.email,'name':u.name}
@router.post('/login')
def login(data:Login,response:Response,db:Session=Depends(get_db)):
    u=db.query(User).filter_by(email=data.email.lower()).first()
    if not u or not u.password_hash or not verify_password(data.password,u.password_hash): raise HTTPException(401,'Invalid email or password')
    set_tokens(response,u); return {'id':u.id,'email':u.email,'name':u.name}
@router.post('/logout')
def logout(response:Response): response.delete_cookie('access_token'); response.delete_cookie('refresh_token'); return {'ok':True}
@router.get('/me')
def me(user=Depends(current_user)): return {'id':user.id,'email':user.email,'name':user.name}
