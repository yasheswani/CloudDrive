from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from app.core.db import Base,engine
from app.core.config import settings
from app.routes import auth,files,folders,sharing
import os
Base.metadata.create_all(bind=engine); os.makedirs(settings.STORAGE_DIR,exist_ok=True)
app=FastAPI(title='CloudDrive API',version='1.0.0')
app.add_middleware(CORSMiddleware,allow_origins=[settings.FRONTEND_ORIGIN],allow_credentials=True,allow_methods=['*'],allow_headers=['*'])
app.state.limiter=Limiter(key_func=get_remote_address); app.add_middleware(SlowAPIMiddleware)
app.include_router(auth.router); app.include_router(files.router); app.include_router(folders.router); app.include_router(sharing.router)
@app.get('/health')
def health(): return {'status':'ok','service':'clouddrive-api'}
