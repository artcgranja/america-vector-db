# src/app/main.py
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.app.api.documents import router as documents_router
from src.app.core.config import settings

app = FastAPI(
    title="Vector Service",
    version="1.0.0",
    description="Micro-serviço para ingestão, vetorização e sumarização de documentos",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar rotas
app.include_router(documents_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)