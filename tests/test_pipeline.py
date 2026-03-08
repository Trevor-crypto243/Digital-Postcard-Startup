import pytest
from src.models.schemas import PostcardSubmission, QAStatus
from src.engine.pipeline import create_postcard_pipeline

@pytest.fixture
def pipeline():
    return create_postcard_pipeline()

@pytest.mark.asyncio
async def test_deterministic_validation_too_short(pipeline):
    submission = PostcardSubmission(id="1", user_id="u1", text_content="Hi")
    with pytest.raises(Exception, match="must be at least 5 characters long"):
        await pipeline.execute(submission)

@pytest.mark.asyncio
async def test_deterministic_validation_too_long(pipeline):
    submission = PostcardSubmission(id="2", user_id="u2", text_content="A" * 1001)
    with pytest.raises(Exception, match="exceeds maximum length"):
        await pipeline.execute(submission)

@pytest.mark.asyncio
async def test_pipeline_without_openai_key_falls_back(pipeline, monkeypatch):
    """
    If no OPENAI API KEY is provided, or network fails, 
    the fallback control gate should catch it and return NEEDS_REVIEW.
    We simulate this by overwriting the evaluation chain to None.
    """
    import src.agent.llm_step
    # Mock the chain as unavailable to trigger the explicit fallback
    monkeypatch.setattr(src.agent.llm_step, "evaluation_chain", None)
    
    submission = PostcardSubmission(id="3", user_id="u3", text_content="Hello, this is a test postcard.")
    result = await pipeline.execute(submission)
    
    assert result.submission_id == "3"
    assert result.evaluation.status == QAStatus.NEEDS_REVIEW
    assert "System Error" in result.evaluation.reasoning
