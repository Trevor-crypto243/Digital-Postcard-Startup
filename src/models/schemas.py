from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from enum import Enum

class QAStatus(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NEEDS_REVIEW = "NEEDS_REVIEW"

class PostcardSubmission(BaseModel):
    id: str = Field(..., description="Unique ID for the postcard submission")
    user_id: str = Field(..., description="ID of the user submitting the postcard")
    text_content: str = Field(..., description="The main text message of the postcard")
    image_url: Optional[HttpUrl] = Field(None, description="Optional image URL for the postcard")

class PostcardEvaluation(BaseModel):
    status: QAStatus = Field(..., description="The final status of the evaluation")
    reasoning: str = Field(..., description="explanation for why this status was chosen")
    suggested_corrections: Optional[str] = Field(None, description="Suggested corrections if any issues were found")

class PipelineResponse(BaseModel):
    submission_id: str
    evaluation: PostcardEvaluation
    processed_at: str
    metadata: dict = Field(default_factory=dict)
