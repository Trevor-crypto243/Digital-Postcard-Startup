import sys
from loguru import logger

# Configuration for Production-level logging
logger.remove()
logger.add(sys.stderr, format="<green>{time}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>", level="INFO")

def get_logger(name: str):
    return logger.bind(name=name)

# Example Usage
if __name__ == "__main__":
    log = get_logger("reliability")
    log.info("Reliability module initialized.")
