from fastapi import FastAPI
from src.routes import transactions, treasury, allocation_rules
from src.config import settings


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI app instance
    """
    app = FastAPI(
        title="Ledger API v1",
        description="Quantum Pi Forge Ledger API - Single source of truth for accounts, transactions, and allocations",
        version="1.0.0",
        debug=settings.env == "development"
    )
    
    # Include routers
    app.include_router(transactions.router)
    app.include_router(treasury.router)
    app.include_router(allocation_rules.router)
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "env": settings.env}
    
    return app


# Create app instance
app = create_app()
