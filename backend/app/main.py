"""
Main FastAPI Application Entrypoint for Vintage Brechó.
Configures lifespan, CORS middleware, API routers, and health check diagnostics.
"""

import logging
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Ensure environment variables are loaded
load_dotenv()

try:
    from app.config import settings
    from app.database import engine, get_db, init_db, dispose_engines
    from app.routers import admin, checkout, products, webhooks
except ImportError:
    from backend.app.config import settings
    from backend.app.database import engine, get_db, init_db, dispose_engines
    from backend.app.routers import admin, checkout, products, webhooks

logger = logging.getLogger("vintage_brecho")
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia ciclo de vida da aplicação: inicialização de banco e encerramento limpo."""
    logger.info("Iniciando Vintage Brechó API...")
    try:
        await init_db()
        logger.info("Banco de dados inicializado com sucesso.")
    except Exception as exc:
        logger.error(f"Erro ao inicializar banco de dados: {exc}")

    yield

    logger.info("Encerrando conexões com o banco de dados...")
    await dispose_engines()
    logger.info("Aplicação finalizada.")


app = FastAPI(
    title="Vintage Brechó API",
    description="API de moda feminina vintage com peças 1-of-1, trava atômica de 10 minutos e checkout PIX",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Configuration
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    settings.FRONTEND_URL,
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permite requisições vindas de qualquer domínio (Vercel, localhost, etc.)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# API Routers
app.include_router(products.router, prefix="/api")
app.include_router(checkout.router, prefix="/api")
app.include_router(webhooks.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


@app.get("/", tags=["health"])
async def root():
    return {
        "app": "Vintage Brechó API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "status": "online",
    }


@app.get("/health", tags=["health"])
@app.get("/api/health", tags=["health"])
async def health_check(db: AsyncSession = Depends(get_db)):
    """Verifica liveness e conectividade com a camada de dados."""
    try:
        await db.execute(text("SELECT 1"))
        return {
            "status": "ok",
            "database": "connected",
            "app": "Vintage Brechó API",
            "version": "1.0.0",
        }
    except Exception as exc:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "degraded",
                "database": "disconnected",
                "error": str(exc),
            },
        )
