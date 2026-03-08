# Digital Postcard Automation Pipeline

This repository contains the Agentic Systems Engineer build task: an automated Postcard Content QA pipeline.

## Quick Start
1.  **Environment**: `python3 -m venv venv && source venv/bin/activate`
2.  **Dependencies**: `pip install -r requirements.txt`
3.  **Configuration**: Create a `.env` file at the root.
    ```env
    OPENAI_API_KEY="your-api-key-here"
    ```

## Running the API
Start the FastAPI server:
```bash
python -m src.main
```
The API will be available at `http://localhost:8000/api/v1/postcards/evaluate`.
You can view the Swagger UI at `http://localhost:8000/docs`.

### Example Request
```bash
curl -X POST "http://localhost:8000/api/v1/postcards/evaluate" \
     -H "Content-Type: application/json" \
     -d '{"id": "pc-123", "user_id": "u-456", "text_content": "Happy Birthday! Have a wonderful day."}'
```

## Architecture
- `src/config_runner.py`: A generic, reusable `WorkflowRunner` that meets the "system that builds systems" requirement.
- `src/pipeline.py`: The concrete implementation of the Postcard QA workflow composed of validation, LLM evaluation, and action steps.
- `src/llm_step.py`: The LangChain structured output parsing layer.
- `src/api.py`: The external-facing API layer.

## Testing
Run the verification suite:
```bash
PYTHONPATH=. pytest -v tests/
```

