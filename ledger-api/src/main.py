"""Ledger API - Main application entry point."""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import logging

from .config import settings
from .db import engine, Base
from .routes import (
    transactions_router,
    treasury_router,
    allocation_rules_router
)
from .schemas.schemas import HealthResponse

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="""
    Ledger API - A comprehensive double-entry accounting system
    
    ## Features
    
    * **Transactions**: Create and manage double-entry transactions
    * **Treasury**: Track treasury accounts and balances
    * **Allocation Rules**: Automatic transaction allocation with JSONB rules
    * **Reconciliation**: Built-in reconciliation workflows
    * **Audit Trail**: Complete audit logging for compliance
    
    ## Authentication
    
    Most endpoints require authentication via Bearer token.
    Set `AUTH_ENABLED=false` in environment for development without auth.
    """,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle database errors."""
    logger.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": "Database error occurred",
            "detail": str(exc) if settings.LOG_LEVEL == "DEBUG" else "Internal server error"
        }
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle validation errors."""
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "message": "Validation error",
            "detail": str(exc)
        }
    )


# Include routers
app.include_router(transactions_router)
app.include_router(treasury_router)
app.include_router(allocation_rules_router)


# Root endpoints
@app.get("/", tags=["root"])
async def root():
    """Root endpoint - API information."""
    return {
        "service": settings.API_TITLE,
        "version": settings.API_VERSION,
        "status": "online",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["root"])
async def health_check():
    """Health check endpoint."""
    # Test database connection
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    return HealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        version=settings.API_VERSION,
        database=db_status,
        timestamp=datetime.now()
    )


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info(f"Starting {settings.API_TITLE} v{settings.API_VERSION}")
    logger.info(f"Authentication: {'Enabled' if settings.AUTH_ENABLED else 'Disabled'}")
    logger.info(f"Database: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'configured'}")
    
    # Note: In production, use Alembic migrations instead of create_all
    # This is here for development convenience only
    # Base.metadata.create_all(bind=engine)


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info(f"Shutting down {settings.API_TITLE}")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )
