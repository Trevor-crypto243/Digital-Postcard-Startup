import pytest
from src.engine.base import BaseWorkflow
from src.utils.reliability import with_retry
import asyncio

def test_workflow_base():
    workflow = BaseWorkflow(id="test-1")
    workflow.add_step("Step 1")
    assert len(workflow.steps) == 1
    assert workflow.steps[0].name == "Step 1"
    
    workflow.mark_step_completed("Step 1")
    assert workflow.steps[0].status == "COMPLETED"

@pytest.mark.asyncio
async def test_retry_success():
    call_count = 0
    async def mock_func():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ValueError("First attempt fails")
        return "Success"
    
    result = await with_retry(mock_func, max_retries=3, delay=0.1)
    assert result == "Success"
    assert call_count == 2
