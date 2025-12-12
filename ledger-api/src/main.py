"""
Main FastAPI application for Ledger API.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config import settings
from src.routes import transactions, treasury, allocation_rules, workflow_patches

# Create FastAPI app
app = FastAPI(
    title="Ledger API",
    description="Single source of truth ledger for logical accounts, transactions, and allocation rules",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(transactions.router, prefix=settings.API_V1_PREFIX)
app.include_router(treasury.router, prefix=settings.API_V1_PREFIX)
app.include_router(allocation_rules.router, prefix=settings.API_V1_PREFIX)
app.include_router(workflow_patches.router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "Ledger API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "ledger-api"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
