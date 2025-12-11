"""
Authentication Dependencies

JWT-based authentication with role-based access control
"""
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from typing import Optional, List
from datetime import datetime, timedelta

from ..config import settings


# Security scheme
security = HTTPBearer()


class AuthenticationError(HTTPException):
    """Raised when authentication fails"""
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationError(HTTPException):
    """Raised when user lacks required permissions"""
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class TokenPayload:
    """JWT token payload"""
    def __init__(self, sub: str, roles: List[str], exp: Optional[datetime] = None):
        self.sub = sub  # Subject (user ID or username)
        self.roles = roles
        self.exp = exp


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token
    
    Args:
        data: Token payload data
        expires_delta: Optional expiration time delta
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.GUARDIAN_JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> TokenPayload:
    """
    Decode and validate JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        TokenPayload with user information
        
    Raises:
        AuthenticationError: If token is invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.GUARDIAN_JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        sub: str = payload.get("sub")
        if sub is None:
            raise AuthenticationError("Token missing subject")
        
        roles: List[str] = payload.get("roles", [])
        exp_timestamp = payload.get("exp")
        exp = datetime.fromtimestamp(exp_timestamp) if exp_timestamp else None
        
        return TokenPayload(sub=sub, roles=roles, exp=exp)
    
    except JWTError as e:
        raise AuthenticationError(f"Invalid token: {str(e)}")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenPayload:
    """
    Dependency to get current authenticated user
    
    Usage:
        @app.get("/protected")
        async def protected_route(user: TokenPayload = Depends(get_current_user)):
            return {"user": user.sub}
    
    Args:
        credentials: HTTP Bearer credentials
        
    Returns:
        TokenPayload with user information
        
    Raises:
        AuthenticationError: If authentication fails
    """
    token = credentials.credentials
    return decode_token(token)


async def get_current_user_optional(
    authorization: Optional[str] = Header(None)
) -> Optional[TokenPayload]:
    """
    Dependency to get current user if authenticated, None otherwise
    
    Args:
        authorization: Optional Authorization header
        
    Returns:
        TokenPayload if authenticated, None otherwise
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization.replace("Bearer ", "")
    try:
        return decode_token(token)
    except AuthenticationError:
        return None


def require_role(required_roles: List[str]):
    """
    Dependency factory to require specific roles
    
    Usage:
        @app.delete("/admin/data")
        async def admin_only(user: TokenPayload = Depends(require_role(["admin"]))):
            return {"status": "deleted"}
    
    Args:
        required_roles: List of roles, user must have at least one
        
    Returns:
        Dependency function
    """
    async def role_checker(user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
        if not any(role in user.roles for role in required_roles):
            raise AuthorizationError(
                f"Required roles: {required_roles}. User has: {user.roles}"
            )
        return user
    
    return role_checker


# Common role dependencies
require_admin = require_role(["admin"])
require_admin_or_operator = require_role(["admin", "operator"])
