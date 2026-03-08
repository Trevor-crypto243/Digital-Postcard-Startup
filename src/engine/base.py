from pydantic import BaseModel, Field
from typing import Generic, TypeVar, List, Optional
from datetime import datetime
from src.utils.logger import get_logger

T = TypeVar("T")

logger = get_logger("workflow")

class WorkflowStep(BaseModel):
    name: str
    status: str = "PENDING"  # PENDING, IN_PROGRESS, COMPLETED, FAILED
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[dict] = None

class BaseWorkflow(BaseModel, Generic[T]):
    """Base class for deterministic workflows."""
    id: str
    steps: List[WorkflowStep] = []
    
    def add_step(self, name: str, metadata: Optional[dict] = None):
        step = WorkflowStep(name=name, metadata=metadata)
        self.steps.append(step)
        logger.info(f"Step added: {name}")
        return step

    def mark_step_completed(self, name: str, metadata: Optional[dict] = None):
        for step in self.steps:
            if step.name == name:
                step.status = "COMPLETED"
                step.metadata = metadata or step.metadata
                logger.info(f"Step completed: {name}")
                return
        logger.warning(f"Step not found: {name}")

    def mark_step_failed(self, name: str, error: str):
        for step in self.steps:
            if step.name == name:
                step.status = "FAILED"
                step.metadata = {"error": error}
                logger.error(f"Step failed: {name} - {error}")
                return
        logger.warning(f"Step not found: {name}")
