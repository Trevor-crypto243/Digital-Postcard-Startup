from datetime import datetime
from src.models.schemas import PostcardSubmission, PostcardEvaluation, QAStatus, PipelineResponse
from src.engine.config_runner import WorkflowRunner
from src.utils.logger import get_logger
from src.agent.llm_step import evaluate_postcard_text

logger = get_logger("postcard_pipeline")

# -------------------------------------------------------------------
# Pipeline Steps
# -------------------------------------------------------------------

def validate_input(submission: PostcardSubmission) -> PostcardSubmission:
    """Deterministic step: Validate basic constraints before hitting the LLM."""
    if not submission.text_content or len(submission.text_content.strip()) < 5:
        logger.warning(f"Submission {submission.id} failed validation: Text too short or empty.")
        # We raise a ValueError to halt the pipeline. The API layer should catch this.
        raise ValueError("Postcard text must be at least 5 characters long.")
    
    if len(submission.text_content) > 1000:
        logger.warning(f"Submission {submission.id} failed validation: Text too long.")
        raise ValueError("Postcard text exceeds maximum length of 1000 characters.")
        
    return submission

async def llm_evaluation_step(submission: PostcardSubmission) -> dict:
    """LLM Step: Request evaluation from the LLM."""
    # Control gate is handled within evaluate_postcard_text (fallback to NEEDS_REVIEW on schema fail)
    evaluation = await evaluate_postcard_text(submission.text_content)
    
    return {
        "submission": submission,
        "evaluation": evaluation
    }

def take_action_step(data: dict) -> PipelineResponse:
    """Action step: Simulate writing to a database or sending an email based on the outcome."""
    submission: PostcardSubmission = data["submission"]
    evaluation: PostcardEvaluation = data["evaluation"]
    
    # Simulate saving to DB
    logger.info(f"Simulating DB Write: Saving evaluation result '{evaluation.status}' for submission '{submission.id}'")
    
    # Simulate automated Notification/Action
    if evaluation.status == QAStatus.REJECTED:
        logger.warning(f"Simulating Action: Sending policy violation email to user {submission.user_id}")
    elif evaluation.status == QAStatus.NEEDS_REVIEW:
        logger.info(f"Simulating Action: Creating a Zendesk ticket for manual review (Submission ID: {submission.id})")
    else:
        logger.info(f"Simulating Action: Enqueueing postcard {submission.id} for final rendering.")

    return PipelineResponse(
        submission_id=submission.id,
        evaluation=evaluation,
        processed_at=datetime.utcnow().isoformat() + "Z",
        metadata={"processed_by": "Agentic_QA_Pipeline_v1"}
    )

# -------------------------------------------------------------------
# Pipeline Factory
# -------------------------------------------------------------------

def create_postcard_pipeline() -> WorkflowRunner:
    """
    Assembles and returns the Postcard QA Pipeline.
    """
    runner = WorkflowRunner(workflow_id="postcard-qa-pipeline")
    
    # Step 1: Deterministic validation (guardrails)
    runner.add_step(
        name="deterministic_validation",
        action=validate_input,
        is_async=False
    )
    
    # Step 2: LLM Classification
    runner.add_step(
        name="llm_evaluation",
        action=llm_evaluation_step,
        is_async=True
    )
    
    # Step 3: Take Automated Action
    runner.add_step(
        name="take_automated_action",
        action=take_action_step,
        is_async=False
    )
    
    return runner
