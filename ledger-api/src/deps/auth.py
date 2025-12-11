"""
Authentication dependencies
Provides API key authentication for endpoints
"""
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from config import settings
import logging

logger = logging.getLogger(__name__)

# API Key header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Verify API key from request header
    
    Args:
        api_key: API key from X-API-Key header
        
    Returns:
        API key if valid
        
    Raises:
        HTTPException: If API key is invalid or missing
    """
    if not api_key:
        logger.warning("API key missing from request")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required"
        )
    
    if api_key != settings.API_KEY:
        logger.warning(f"Invalid API key attempted: {api_key[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return api_key


def get_current_user(api_key: str = Security(verify_api_key)) -> str:
    """
    Get current user from API key
    In a real implementation, this would map API key to user identity
    
    Args:
        api_key: Verified API key
        
    Returns:
        User identifier
    """
    # In production, this would look up the user associated with the API key
    # For now, we return a default user
    return "api_user"
