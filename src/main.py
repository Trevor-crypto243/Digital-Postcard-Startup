import uvicorn
from fastapi import FastAPI
from src.utils.logger import get_logger
from src.api.routes import router as postcards_router
from src.api.limiter import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

logger = get_logger("main")

# Load environment variables (OPENAI_API_KEY)
load_dotenv()

from contextlib import asynccontextmanager
from src.agent.llm_step import get_graph_app

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize LangGraph Checkpointer at startup
    logger.info("Initializing LangGraph Checkpointer...")
    await get_graph_app()
    yield
    logger.info("Shutting down...")

app = FastAPI(
    title="Digital Postcard Automation API",
    description="Agentic pipeline for Postcard Content QA",
    version="1.0.0",
    lifespan=lifespan
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

