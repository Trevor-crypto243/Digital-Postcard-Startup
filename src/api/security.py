from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from typing import Optional

# Security and Authentication Concepts
# In a real production environment, this would validate JWTs, connect to an Identity Provider,
# and check specific granular permission scopes required for tools (e.g., 'tools:slack:write').

API_KEY_NAME = "X-Agentic-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Dummy valid keys for the interview simulation
VALID_API_KEYS = {
    "agentic-demo-key-123": {"role": "admin", "permissions": ["all"]},
    "limited-key-456": {"role": "user", "permissions": ["read-only"]}
}

async def get_current_user(api_key: Optional[str] = Security(api_key_header)):
    """
    Mock Authentication Dependency.
    Ensures safe tool execution by validating identity before the pipeline runs.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key in headers",
        )
    
    user_data = VALID_API_KEYS.get(api_key)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key",
        )
        
    return user_data

def require_admin(user_data: dict = Security(get_current_user)):
    """
    Mock Scoped Permission Check.
    Ensures the caller has administrative privileges.
    """
    if user_data.get("role") != "admin":
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requires Admin Role permissions.",
        )
    return user_data
