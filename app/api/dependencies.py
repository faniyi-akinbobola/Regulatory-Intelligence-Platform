from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer_scheme = HTTPBearer(auto_error=False)

# Auth
async def get_optional_user(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)
) -> dict | None:
    """
    Returns the token payload if a valid Bearer token is provided.
    Returns None if no token is provided.
    This is 'optional' auth - routes work with or without a logged-in user.
    """
    if credentials is None:
        return None
    
    # Token verification will be wired up once the DB layer is ready
    # For now we return a placeholder so routes don't break 
    return {"token": credentials.credentials}

async def get_current_user(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)
) -> dict:
    """
    Enforces authentication - raises 401 if no token is provided.
    Use this on routes that require a logged-in user.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"token": credentials.credentials}

OptionalUser = Annotated[dict | None, Depends(get_optional_user)]
CurrentUser = Annotated[dict, Depends(get_current_user)]



    
