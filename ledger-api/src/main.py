"""Ledger API - Main Application Entry Point"""

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from config import settings
from routes import transactions, treasury, allocation_rules

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.API_TITLE} v{settings.API_VERSION}")
    logger.info(f"Guardian wallet: {settings.GUARDIAN_WALLET_ADDRESS}")
    
    if settings.RECONCILIATION_CRON_ENABLED:
        logger.info(f"Reconciliation scheduled every {settings.RECONCILIATION_INTERVAL_HOURS} hours")
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.API_TITLE}")


# Initialize FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    debug=settings.API_DEBUG,
    lifespan=lifespan
)

# Configure CORS with allowed origins from settings
allowed_origins = settings.ALLOWED_ORIGINS.split(",") if settings.ALLOWED_ORIGINS else []
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(transactions.router)
app.include_router(treasury.router)
app.include_router(allocation_rules.router)


@app.get("/", tags=["health"])
async def root():
    """Root endpoint - API information"""
    return {
        "api": settings.API_TITLE,
        "version": settings.API_VERSION,
        "status": "online",
        "description": settings.API_DESCRIPTION,
        "documentation": "/docs"
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    # TODO: Add database connectivity check
    return {
        "status": "healthy",
        "version": settings.API_VERSION,
        "database": "connected"  # Placeholder
    }


@app.get("/api/v1/info", tags=["info"])
async def api_info():
    """API information and endpoints"""
    return {
        "api": settings.API_TITLE,
        "version": settings.API_VERSION,
        "endpoints": {
            "transactions": "/api/v1/transactions",
            "treasury": "/api/v1/treasury",
            "allocation_rules": "/api/v1/allocation-rules"
        },
        "features": [
            "Double-entry bookkeeping",
            "Automated allocation rules",
            "Treasury management",
            "Audit logging",
            "Reconciliation services"
        ]
    }


# Exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle ValueError exceptions"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal error occurred"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_DEBUG
    )
