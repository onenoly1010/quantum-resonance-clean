"""Authentication dependencies for API endpoints"""

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from config import settings

# Security scheme
security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time delta
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Verify JWT token and return payload.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        Token payload
        
    Raises:
        HTTPException: If token is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        raise credentials_exception


def get_current_user(token_payload: dict = Depends(verify_token)) -> str:
    """
    Get current user from token payload.
    
    Args:
        token_payload: Decoded token payload
        
    Returns:
        User identifier
    """
    user = token_payload.get("sub")
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    return user


def require_guardian_role(
    current_user: str = Depends(get_current_user),
    token_payload: dict = Depends(verify_token)
) -> str:
    """
    Require guardian role for sensitive operations.
    
    Args:
        current_user: Current user identifier
        token_payload: Decoded token payload
        
    Returns:
        User identifier if authorized
        
    Raises:
        HTTPException: If user doesn't have guardian role
    """
    roles = token_payload.get("roles", [])
    if "guardian" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Guardian role required for this operation"
        )
    return current_user


# Optional authentication (allows unauthenticated access but provides user if authenticated)
async def get_optional_user(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """
    Get current user if authenticated, None otherwise.
    
    Args:
        authorization: Optional authorization header
        
    Returns:
        User identifier or None
    """
    if not authorization:
        return None
    
    try:
        # Extract token from "Bearer <token>"
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload.get("sub")
    except:
        return None
