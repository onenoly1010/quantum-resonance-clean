from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from src.config import settings

security = HTTPBearer()


async def get_current_actor(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Decode and validate JWT token to get current actor information.
    
    Args:
        credentials: HTTP Bearer credentials containing JWT token
        
    Returns:
        Decoded JWT payload containing actor information
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials
    
    try:
        payload = jwt.decode(
            token,
            settings.guardian_jwt_secret,
            algorithms=["HS256"]
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def require_guardian_role(
    actor: dict = Depends(get_current_actor)
) -> dict:
    """
    Require that the current actor has guardian role.
    
    Args:
        actor: Current actor from JWT token
        
    Returns:
        Actor information if guardian role is present
        
    Raises:
        HTTPException: If guardian role is not present
    """
    roles = actor.get("roles", [])
    
    if "guardian" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Guardian role required"
        )
    
    return actor
