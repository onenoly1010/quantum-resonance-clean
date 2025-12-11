"""Authentication dependencies."""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from typing import Optional
from datetime import datetime, timedelta

from ..config import settings


security = HTTPBearer(auto_error=False)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in token
        expires_delta: Token expiration time
    
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT access token.
    
    Args:
        token: JWT token to decode
    
    Returns:
        Decoded token data
    
    Raises:
        HTTPException: If token is invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """
    Get current user from JWT token.
    
    Args:
        request: FastAPI request object
        credentials: HTTP bearer credentials
    
    Returns:
        User data from token or None if auth disabled
    
    Raises:
        HTTPException: If authentication fails
    """
    # If auth is disabled, return mock user
    if not settings.AUTH_ENABLED:
        return {
            "user_id": "system",
            "username": "system",
            "roles": ["admin"]
        }
    
    # Check for credentials
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Decode token
    token_data = decode_access_token(credentials.credentials)
    
    return {
        "user_id": token_data.get("sub"),
        "username": token_data.get("username"),
        "roles": token_data.get("roles", [])
    }


async def get_optional_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """
    Get current user if authenticated, otherwise return None.
    
    Args:
        request: FastAPI request object
        credentials: HTTP bearer credentials
    
    Returns:
        User data from token or None
    """
    if not settings.AUTH_ENABLED:
        return {
            "user_id": "system",
            "username": "system",
            "roles": ["admin"]
        }
    
    if credentials is None:
        return None
    
    try:
        token_data = decode_access_token(credentials.credentials)
        return {
            "user_id": token_data.get("sub"),
            "username": token_data.get("username"),
            "roles": token_data.get("roles", [])
        }
    except HTTPException:
        return None


def require_role(required_role: str):
    """
    Dependency to require a specific role.
    
    Args:
        required_role: Role required to access endpoint
    
    Returns:
        Dependency function
    """
    async def role_checker(user: dict = Depends(get_current_user)):
        if not settings.AUTH_ENABLED:
            return user
        
        user_roles = user.get("roles", [])
        if required_role not in user_roles and "admin" not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required"
            )
        return user
    
    return role_checker
