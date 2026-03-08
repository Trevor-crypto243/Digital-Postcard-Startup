from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

# Rate Limiter setup
# We use IP address to rate limit users to prevent abuse.
limiter = Limiter(key_func=get_remote_address)
