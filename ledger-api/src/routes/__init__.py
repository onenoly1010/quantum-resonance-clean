"""Routes package."""

from .transactions import router as transactions_router
from .treasury import router as treasury_router
from .allocation_rules import router as allocation_rules_router

__all__ = [
    "transactions_router",
    "treasury_router", 
    "allocation_rules_router"
]
