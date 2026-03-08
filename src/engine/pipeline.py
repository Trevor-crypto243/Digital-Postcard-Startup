from datetime import datetime
from src.models.schemas import PostcardSubmission, PostcardEvaluation, QAStatus, PipelineResponse
from src.engine.config_runner import WorkflowRunner
from src.utils.logger import get_logger
from src.agent.llm_step import evaluate_postcard_text
from src.agent.tools import send_slack_alert, send_email_to_user

from src.config import settings

logger = get_logger("postcard_pipeline")

# -------------------------------------------------------------------
# Pipeline Steps
# -------------------------------------------------------------------

async def validate_input(submission: PostcardSubmission) -> PostcardSubmission:
    """Deterministic step: Validate basic constraints before hitting the LLM."""
    if not submission.text_content or len(submission.text_content.strip()) < settings.MIN_TEXT_LENGTH:
        logger.warning(f"Submission {submission.id} failed validation: Text too short or empty.")
        raise ValueError(f"Postcard text must be at least {settings.MIN_TEXT_LENGTH} characters long.")
    
    if len(submission.text_content) > settings.MAX_TEXT_LENGTH:
        logger.warning(f"Submission {submission.id} failed validation: Text too long.")
        raise ValueError(f"Postcard text exceeds maximum length of {settings.MAX_TEXT_LENGTH} characters.")
        
    return submission

async def llm_evaluation_step(submission: PostcardSubmission) -> dict:
    """LLM Step: Request evaluation from the LLM."""
    # Control gate is handled within evaluate_postcard_text (fallback to NEEDS_REVIEW on schema fail)
    # Agentic Intelligence Step (LLM Evaluation with Persistent Memory)
    # We pass the submission_id as the thread_id for state tracking
    logger.info(f"[Step 2] Routing to LLM Agent (Thread ID: {submission.id})")
    evaluation = await evaluate_postcard_text(submission.text_content, thread_id=submission.id)
    
    return {
        "submission": submission,
        "evaluation": evaluation
    }

async def take_action_step(data: dict) -> PipelineResponse:
    """Action step: Dispatch notifications and record results."""
    submission: PostcardSubmission = data["submission"]
    evaluation: PostcardEvaluation = data["evaluation"]
    
    logger.info(f"Simulating DB Write: Saving evaluation result '{evaluation.status}' for submission '{submission.id}'")
    
    # Real Notification Dispatch (using our defined tools)
    if evaluation.status == QAStatus.REJECTED:
        send_email_to_user.invoke({
            "user_id": submission.user_id,
            "subject": f"Postcard {submission.id} Rejected",
            "body": f"Your postcard was rejected. Reason: {evaluation.reasoning}"
        })
    elif evaluation.status == QAStatus.NEEDS_REVIEW:
        send_slack_alert.invoke({
            "channel": settings.MODERATION_CHANNEL,
            "message": f"🚨 HUMAN REVIEW REQUIRED: Postcard {submission.id} flagged. Reason: {evaluation.reasoning}",
            "severity": "high"
        })
        # Also notify the moderation team via email
        send_email_to_user.invoke({
            "user_id": "moderators-list",
            "subject": f"Moderation Required: {submission.id}",
            "body": f"A new postcard requires manual review. Thread ID: {submission.id}"
        })
    else:
        logger.info(f"Success: Postcard {submission.id} approved and ready for rendering.")

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
        is_async=True
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
        is_async=True
    )
    
    return runner
