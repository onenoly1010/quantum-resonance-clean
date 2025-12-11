"""Ledger API - Main Application Entry Point"""

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from config import settings
from routes import transactions, treasury, allocation_rules

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    debug=settings.API_DEBUG
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
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


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Actions to perform on application startup"""
    logger.info(f"Starting {settings.API_TITLE} v{settings.API_VERSION}")
    logger.info(f"Guardian wallet: {settings.GUARDIAN_WALLET_ADDRESS}")
    
    # TODO: Initialize database connection pool
    # TODO: Start reconciliation cron if enabled
    if settings.RECONCILIATION_CRON_ENABLED:
        logger.info(f"Reconciliation scheduled every {settings.RECONCILIATION_INTERVAL_HOURS} hours")


@app.on_event("shutdown")
async def shutdown_event():
    """Actions to perform on application shutdown"""
    logger.info(f"Shutting down {settings.API_TITLE}")
    
    # TODO: Close database connections
    # TODO: Stop reconciliation cron


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_DEBUG
    )
