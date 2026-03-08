from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from typing import Optional

# Security and Authentication Concepts
# In a real production environment, this would validate JWTs, connect to an Identity Provider,
# and check specific granular permission scopes required for tools (e.g., 'tools:slack:write').

from src.config import settings

API_KEY_NAME = "X-Agentic-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def require_admin(api_key: str = Security(api_key_header)):
    """
    Dependency to enforce admin access via API Key.
    """
    if api_key == settings.ADMIN_API_KEY:
        return {"user": "Admin", "role": "admin"}
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Unauthorized: Valid Admin API Key required for this operational route."
    )

# Alias for general authentication in this demo
get_current_user = require_admin
