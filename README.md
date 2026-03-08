# Digital Postcard Automation Pipeline (Agentic V2)

This repository contains the advanced Agentic Systems Engineer submission: an automated Postcard Content QA pipeline demonstrating production-level backends, agentic workflow orchestration, LangGraph memory integration, and Human-in-The Loop UI.

## Features & Agentic Interview Criteria Met
- **Production Level Backend**: Docker Compose (App + PostgreSQL), FastAPI with standard Security/Authentication/CORS, and SlowAPI Rate-Limiting.
- **Agentic Workflow**: Uses LangGraph to orchestrate complex reasoning instead of linear chains.
- **Service Integration & Tooling**: Agent is equipped with LangChain tools (`SendSlackAlert`, `SendEmail`) to dynamically decide operational routing.
- **Memory & Statefulness**: Uses `langgraph-checkpoint-postgres` to persist decision metadata, RCA evidence, and workflow states mimicking an "order journey" in Ecommerce.
- **Human-in-Loop (HITL)**: Workflow pauses execution for `NEEDS_REVIEW` scenarios, awaiting manual human override via a Streamlit UI interface.

## Quick Start
1.  **Environment Setup**: Install Python 3.13 and Docker.
    ```bash
    python3 -m venv venv && source venv/bin/activate
    pip install -r requirements.txt
    ```
2.  **Configuration**: Create a `.env` file at the root.
    ```env
    OPENAI_API_KEY="your-api-key-here"
    ```
3.  **Start Infrastructure**:
    ```bash
    make up
    ```
    This spins up the PostgreSQL database and the FastAPI backend. The API will be available at `http://localhost:8000/docs`.

## Running the API & Local Testing
We use an authenticated endpoint (`X-Agentic-API-Key: agentic-demo-key-123`) to enforce Safe Tool Execution.
```bash
curl -X POST "http://localhost:8000/api/v1/postcards/evaluate" \
     -H "Content-Type: application/json" \
     -H "X-Agentic-API-Key: agentic-demo-key-123" \
     -d '{"id": "pc-123", "user_id": "u-456", "text_content": "Happy Birthday! Have a wonderful day."}'
```

## Running the human in the loop Interface
To review paused workflows:
```bash
make run-hitl
```
