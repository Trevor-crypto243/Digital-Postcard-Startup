import asyncio
from typing import Callable, Any
from src.utils.logger import get_logger

logger = get_logger("reliability")

async def with_retry(func: Callable, *args, max_retries: int = 3, delay: float = 1.0, **kwargs) -> Any:
    """Retry an async function with exponential backoff."""
    last_exception = None
    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            wait_time = delay * (2 ** attempt)
            logger.warning(f"Attempt {attempt + 1} failed. Retrying in {wait_time}s... Error: {e}")
            await asyncio.sleep(wait_time)
    
    logger.error(f"All {max_retries} attempts failed. Last error: {last_exception}")
    raise last_exception
