import uvicorn
from fastapi import FastAPI
from src.logger import get_logger
from src.api import router as postcards_router
from src.limiter import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

logger = get_logger("main")

# Load environment variables (OPENAI_API_KEY)
load_dotenv()

app = FastAPI(
    title="Digital Postcard Automation API",
    description="Agentic pipeline for Postcard Content QA",
    version="1.0.0"
)

# Standard Security Best Practice: CORS & Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(postcards_router, prefix="/api/v1/postcards")

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    logger.info("Starting up FastAPI server internally...")
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)

