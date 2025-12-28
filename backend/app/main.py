"""FastAPI application entry point."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import gameweeks, players, predictions, sync, backtest
from app.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

settings = get_settings()

app = FastAPI(
    title="FPL Team of the Week Predictor",
    description="Predict the FPL Dream Team (Team of the Week) using ML",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(sync.router, prefix="/api/sync", tags=["sync"])
app.include_router(gameweeks.router, prefix="/api/gameweeks", tags=["gameweeks"])
app.include_router(players.router, prefix="/api/players", tags=["players"])
app.include_router(predictions.router, prefix="/api/predictions", tags=["predictions"])
app.include_router(backtest.router, prefix="/api/backtest", tags=["backtest"])


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.model_version}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "FPL Team of the Week Predictor API",
        "docs": "/docs",
        "health": "/api/health",
    }
