from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, BigInteger, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.db import Base

def now(): return datetime.now(timezone.utc)
class User(Base):
    __tablename__='users'
    id=Column(Integer,primary_key=True); email=Column(String(255),unique=True,index=True,nullable=False); name=Column(String(120),nullable=False); password_hash=Column(String(255),nullable=True); oauth_provider=Column(String(40)); created_at=Column(DateTime(timezone=True),default=now)
class Folder(Base):
    __tablename__='folders'
    id=Column(Integer,primary_key=True); name=Column(String(255),nullable=False); owner_id=Column(Integer,ForeignKey('users.id'),nullable=False); parent_id=Column(Integer,ForeignKey('folders.id'),nullable=True); deleted_at=Column(DateTime(timezone=True)); created_at=Column(DateTime(timezone=True),default=now)
class File(Base):
    __tablename__='files'
    id=Column(Integer,primary_key=True); name=Column(String(255),nullable=False); owner_id=Column(Integer,ForeignKey('users.id'),nullable=False); folder_id=Column(Integer,ForeignKey('folders.id'),nullable=True); storage_key=Column(String(500),nullable=False); mime_type=Column(String(150)); size=Column(BigInteger,default=0); starred=Column(Boolean,default=False); deleted_at=Column(DateTime(timezone=True)); created_at=Column(DateTime(timezone=True),default=now); updated_at=Column(DateTime(timezone=True),default=now,onupdate=now)
class Share(Base):
    __tablename__='shares'; id=Column(Integer,primary_key=True); file_id=Column(Integer,ForeignKey('files.id'),nullable=False); user_id=Column(Integer,ForeignKey('users.id'),nullable=False); role=Column(String(20),default='viewer'); created_at=Column(DateTime(timezone=True),default=now); __table_args__=(UniqueConstraint('file_id','user_id'),)
class LinkShare(Base):
    __tablename__='link_shares'; id=Column(Integer,primary_key=True); file_id=Column(Integer,ForeignKey('files.id'),nullable=False); token=Column(String(80),unique=True,index=True,nullable=False); expires_at=Column(DateTime(timezone=True)); password_hash=Column(String(255)); created_at=Column(DateTime(timezone=True),default=now)
class Star(Base):
    __tablename__='stars'; id=Column(Integer,primary_key=True); file_id=Column(Integer,ForeignKey('files.id'),nullable=False); user_id=Column(Integer,ForeignKey('users.id'),nullable=False); __table_args__=(UniqueConstraint('file_id','user_id'),)
class Activity(Base):
    __tablename__='activities'; id=Column(Integer,primary_key=True); user_id=Column(Integer,ForeignKey('users.id')); action=Column(String(80)); target_type=Column(String(30)); target_id=Column(Integer); metadata_json=Column(Text); created_at=Column(DateTime(timezone=True),default=now)
