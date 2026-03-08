import asyncio
from typing import List, Callable, Any, Dict
from src.base import BaseWorkflow
from src.logger import get_logger

logger = get_logger("workflow_runner")

class WorkflowRunner:
    """
    A reusable runner designed to execute a series of steps in a pipeline.
    Satisfies the 'system that builds systems' requirement.
    New workflows can be assembled in <15 minutes by composing steps.
    """
    def __init__(self, workflow_id: str):
        self.workflow = BaseWorkflow(id=workflow_id)
        self.steps: List[Dict[str, Any]] = []

    def add_step(self, name: str, action: Callable, is_async: bool = False):
        """
        Adds a functional step to the workflow.
        
        Args:
            name: Human readable step name.
            action: A callable that takes previous step's output as input.
            is_async: If the underlying callable is an async function.
        """
        self.workflow.add_step(name=name)
        self.steps.append({
            "name": name,
            "action": action,
            "is_async": is_async
        })
        return self

    async def execute(self, initial_payload: Any) -> Any:
        """
        Executes all configured steps sequentially.
        """
        logger.info(f"Starting execution for workflow: {self.workflow.id}")
        current_payload = initial_payload
        
        for step_config in self.steps:
            name = step_config["name"]
            action = step_config["action"]
            is_async = step_config["is_async"]
            
            logger.info(f"Executing step: {name}")
            try:
                if is_async:
                    current_payload = await action(current_payload)
                else:
                    current_payload = action(current_payload)
                
                # We specifically don't record the full payload metadata 
                # to keep logging clean, but we mark it complete.
                self.workflow.mark_step_completed(name)
            
            except Exception as e:
                error_msg = str(e)
                self.workflow.mark_step_failed(name, error_msg)
                logger.error(f"Workflow {self.workflow.id} failed at step '{name}': {error_msg}")
                raise e # Re-raise to be handled by the API/caller
        
        logger.info(f"Workflow {self.workflow.id} execution completed successfully.")
        return current_payload
