"""
Authentication utilities for Supabase JWT.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Tuple
from supabase import create_client, Client
from app.core.config import settings


security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Verify JWT token and return user ID.
    
    Args:
        credentials: Bearer token credentials
    
    Returns:
        User ID (UUID as string)
    
    Raises:
        HTTPException if token is invalid
    """
    from app.core.supabase import supabase
    token = credentials.credentials
    
    try:
        # Verify token with Supabase
        user = supabase.auth.get_user(token)
        
        if not user or not user.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        return user.user.id
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}"
        )


async def get_user_client(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Tuple[str, Client]:
    """
    Get Supabase client with user's JWT token for RLS.
    
    Args:
        credentials: Bearer token credentials
    
    Returns:
        Tuple of (user_id, supabase_client)
    
    Raises:
        HTTPException if token is invalid
    """
    from app.core.supabase import supabase
    token = credentials.credentials
    
    try:
        # Verify token
        user = supabase.auth.get_user(token)
        
        if not user or not user.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        # Create client with user's JWT token
        user_client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY  # Use anon key, not service role
        )
        user_client.postgrest.auth(token)  # Set the JWT token
        
        return user.user.id, user_client
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}"
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[str]:
    """
    Get user ID if authenticated, None otherwise.
    
    Useful for endpoints that work with or without auth.
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
