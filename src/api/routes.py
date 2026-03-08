from fastapi import APIRouter, HTTPException, BackgroundTasks, Request, Depends
from pydantic import ValidationError
from src.models.schemas import PostcardSubmission, PipelineResponse
from src.engine.pipeline import create_postcard_pipeline
from src.utils.logger import get_logger
from src.api.limiter import limiter
from src.api.security import require_admin, get_current_user

logger = get_logger("api")

router = APIRouter()
pipeline_runner = create_postcard_pipeline()

@router.post("/evaluate", response_model=PipelineResponse)
@limiter.limit("5/minute")
async def evaluate_postcard(
    request: Request,
    submission: PostcardSubmission,
    user_data: dict = Depends(require_admin) # Ensures Safe Tool Execution & Scoped Permissions
):
    """
    Endpoint to receive a postcard submission and trigger the automation pipeline.
    Requires Admin API Key, Rate Limited to 5 requests per minute.
    """
    logger.info(f"Received API request by Admin to evaluate postcard ID: {submission.id}")

    try:
        # Execute the pipeline with the incoming payload
        response = await pipeline_runner.execute(initial_payload=submission)
        return response
        
    except ValueError as ve:
        # Deterministic validation errors (e.g. text too long/short)
        logger.warning(f"API Validation Error for {submission.id}: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
        
    except ValidationError as ve:
        # Schema parsing issues before pipeline
        logger.warning(f"API Pydantic Error for {submission.id}: {ve}")
        raise HTTPException(status_code=422, detail="Invalid data schema format provided.")
        
    except Exception as e:
        # Check if it looks like an authentication error from OpenAI
        error_str = str(e).lower()
        if "api key" in error_str or "unauthorized" in error_str or "401" in error_str:
             logger.error(f"API Configuration/Auth Error for {submission.id}: {e}")
             raise HTTPException(
                 status_code=424, 
                 detail="Pipeline failed due to downstream authentication issue (LLM). Please check API keys."
             )
             
        # Uncaught pipeline failures 
        logger.error(f"API Internal Error while evaluating {submission.id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Internal server error executing pipeline: {type(e).__name__}"
        )
