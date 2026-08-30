from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
class Register(BaseModel): email: EmailStr; name: str=Field(min_length=2,max_length=120); password: str=Field(min_length=8,max_length=128)
class Login(BaseModel): email: EmailStr; password: str
class FolderCreate(BaseModel): name: str=Field(min_length=1,max_length=255); parent_id: int|None=None
class ShareCreate(BaseModel): file_id:int; email:EmailStr; role:str=Field(pattern='^(viewer|editor)$')
class LinkCreate(BaseModel): file_id:int; expires_at:datetime|None=None; password:str|None=None
