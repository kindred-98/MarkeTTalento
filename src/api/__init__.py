"""
MarkeTTalento - FastAPI Backend
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.database.database import engine, Base
from src.api.router import api_router
from src.core.errors import setup_error_handlers
from src.core.logging import setup_logging

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MarkeTTalento API",
    description="Sistema de gestión de inventario inteligente",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_error_handlers(app)
setup_logging()

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "MarkeTTalento API", "version": "1.0.0"}