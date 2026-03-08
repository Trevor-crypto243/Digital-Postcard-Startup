from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import ValidationError
from src.schemas import PostcardSubmission, PipelineResponse
from src.pipeline import create_postcard_pipeline
from src.logger import get_logger

logger = get_logger("api")

router = APIRouter()
pipeline_runner = create_postcard_pipeline()

@router.post("/evaluate", response_model=PipelineResponse)
async def evaluate_postcard(submission: PostcardSubmission):
    """
    Endpoint to receive a postcard submission and trigger the automation pipeline.
    """
    logger.info(f"Received API request to evaluate postcard ID: {submission.id}")
    try:
        # Execute the pipeline with the incoming payload
        response = await pipeline_runner.execute(initial_payload=submission)
        return response
        
    except ValueError as ve:
        # Deterministic validation errors (e.g. text too long/short)
        logger.warning(f"API Bad Request for {submission.id}: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
        
    except ValidationError as ve:
        # Schema parsing issues before pipeline
        logger.warning(f"API Pydantic Error for {submission.id}: {ve}")
        raise HTTPException(status_code=422, detail="Invalid data schema format provided.")
        
    except Exception as e:
        # Uncaught pipeline failures (LLM fallback handles most LLM issues)
        logger.error(f"API Internal Error while evaluating {submission.id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error executing pipeline.")
