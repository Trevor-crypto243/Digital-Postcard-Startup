---

## 💡 Why This Pipeline?
Low-stakes AI (chatbots) can afford to be purely probabilistic. However, **enterprise-grade automation** (like Postcard Content QA) requires a **Deterministic AI Pipeline**. This project was built to solve the "unpredictability" problem of LLMs by:
1.  **Guarding Profits**: Preventing costly printing of policy-violating or invalid postcards.
2.  **Risk Mitigation**: Ensuring hateful or fraudulent content never reaches a customer.
3.  **Human Efficiency**: Automating 90% of binary decisions while routing only the most ambiguous 10% to human experts.

---

## 🏗️ Deterministic AI Pipeline Alignment
This architecture follows the core principles outlined in [Learning to build deterministic AI pipelines with LangChain](https://medium.com/@sajo02/learning-to-build-deterministic-ai-pipelines-with-langchain-a-practical-approach-aec6422c84ef):

- **Deterministic Validation First**: We use standard Python logic (Stage 1) to enforce length and format constraints before a single cent is spent on LLM tokens.
- **Structured Outputs**: Every AI decision is forced into a Pydantic schema using OpenAI's Structured Output API, ensuring zero "parsing errors" in production.
- **Stateful Memory**: Leveraging **LangGraph** with a PostgreSQL checkpointer allows the pipeline to "remember" its state, supporting retries and auditability (the "Order Journey" pattern).
- **Separation of Concerns**: Probabilistic reasoning (agent) is strictly separated from deterministic actions (sending emails/Slack alerts).

---

## 🛠️ Features & Engineering Standards
- **Agentic Orchestration**: Uses **LangGraph** for non-linear, stateful reasoning.
- **Production Resilience**: Implements node-level error handling and non-blocking asynchronous execution.
- **Tool Integration**: Agent dynamically uses Slack and Email tools for operational routing.
- **Memory Persistence**: Uses PostgreSQL to track the "order journey" and maintain context across restarts.
- **Human-in-the-Loop**: Integrated Streamlit dashboard for manual review of flagged content.

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.11+**
- **Docker & Docker Compose**
- **OpenAI API Key**

### 2. Environment Setup
Clone the repository and set up a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configuration
Create your `.env` file from the provided template:
```bash
cp .env.example .env
```
Edit the `.env` file and provide your `OPENAI_API_KEY`. The default database and security settings are pre-configured for local development.

### 4. Start Infrastructure
Launch the PostgreSQL database and the FastAPI application using Docker:
```bash
make up
```
- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Database Port**: `5435` (mapped from `5432` in container)

---

## 🧪 Testing & Verification

### **A. End-to-End Automated Test Suite**
We provide a comprehensive script that tests validation, safe content, rejection logic, and concurrent processing:
```bash
python3 tests/verify_full_functionality.py
```

### **B. Manual Testing (cURL)**
The API uses an authenticated header: `X-Agentic-API-Key: agentic-demo-key-123`.

**Evaluate a Postcard:**
```bash
curl -X POST "http://localhost:8000/api/v1/postcards/evaluate" \
     -H "Content-Type: application/json" \
     -H "X-Agentic-API-Key: agentic-demo-key-123" \
     -d '{"id": "pc-101", "user_id": "u-456", "text_content": "Happy Birthday! Sending love."}'
```

---

## 🤵 Human-in-The-Loop (HITL) Workflow
The system is designed for high-stakes environments where AI decisions require human oversight.

### **Demo Samples Provided:**
To showcase the pipeline's versatility, we have seeded the following cases in the HITL dashboard:
- **`demo-approved-1`**: A standard POSITIVE postcard.
- **`demo-rejected-1`**: A clear SPAM/FRAUD violation.
- **`demo-review-1`**: An AMBIGUOUS/VAGUE message flagging for professional human judgment.
- **`demo-short-1`**: A DETERMINISTIC failure (too short) that never reached the LLM.

### **The "Review to Resolution" Flow:**
1.  **AI Flagging**: If the pipeline results in `NEEDS_REVIEW`, the `take_action_step` is triggered.
2.  **Multichannel Notification**: 
    - **Slack**: A high-priority alert is dispatched to the moderation channel using the `send_slack_alert` tool.
    - **Email**: An automated notification is sent to the moderation team via `send_email_to_user`.
3.  **Manual Review**: The moderator launches the Streamlit app (`make run-hitl`) and selects the relevant `Submission ID`.
4.  **Final Resolution**: 
    - The moderator reviews the AI's reasoning and the postcard content.
    - A human decision (**APPROVE** or **REJECT**) is submitted.
    - **Audit Trail**: The decision is persisted in a `human_reviews` audit table, ensuring full traceability for compliance.

---

## 🤵 Human-in-The-Loop (HITL) App
When the AI flags content for manual review (`NEEDS_REVIEW`), use the Streamlit interface to resolve it:

1.  **Launch the App**:
    ```bash
    make run-hitl
    ```
2.  **Access the Dashboard**: Open your browser at [http://localhost:8501](http://localhost:8501).

---

---

## 🏗️ Repository Architecture
- `/src/agent`: LangGraph state machine, nodes, and LLM tools.
- `/src/api`: FastAPI routes, security dependencies, and middleware.
- `/src/engine`: Core workflow orchestration and pipeline runner.
- `/infra`: Docker and database configurations.

---

## 🧠 Architectural Justification & Technical Decisions

### 1. Why LangChain & LangGraph?
While simpler frameworks exist, **LangGraph** was chosen because it treats agentic workflows as **stateful graphs** rather than linear chains.
- **Cycles & Recursion**: Real-world QA requires loops (e.g., "retry if tool fails" or "refine if evaluation is borderline"). LangGraph handles this naturally.
- **Granular Control**: Unlike "Blackbox" agents (AutoGPT), LangGraph allows us to define rigid nodes (validation) alongside flexible ones (agent reasoning).
- **LangSmith Integration**: Provides production-grade observability, allowing us to debug specific nodes in a complex trace and optimize costs.

### 2. Scalability & Performance
The application is designed to support thousands of concurrent users through:
- **Asynchronous Execution**: Every step in the pipeline is `async`. Slow I/O (Database, LLMs) does not block the event loop, allowing the FastAPI server to handle a high volume of requests on minimal hardware.
- **Thread Pooling**: Synchronous legacy code or CPU-bound tasks are offloaded to `asyncio.to_thread`, preventing event loop starvation.
- **PostgreSQL Persistence**: Using a robust relational DB instead of local files ensures that state is persistent, queryable, and horizontally scalable.

### 3. Security & Robustness
- **Safe Tool Execution**: All agent tools (Slack, Email) require an authenticated API context. The agent cannot "jailbreak" and call these tools without passing through our security middleware.
- **Node-Level Resilience**: Every LLM call is wrapped in a fallback layer. If OpenAI is down or the quota is hit (HTTP 429), the system **fails gracefully** by flagging the item for manual review instead of returning a 500.
- **Exponential Backoff**: Implements `with_retry` logic for all LLM nodes. This ensures the system automatically recovers from transient network issues or rate-limit "bursts" without user intervention.
- **Environment Management**: Secrets are strictly separated via `.env` and `.env.example`, with Git safeguards in place to prevent accidental leaks.

### 4. Evaluation-Driven Development (EDD)
Unlike traditional software, AI systems require probabilistic testing. This repository includes a semi-automated **LLM-as-a-Judge** suite:
- **Golden Set**: A curated set of high-variance inputs (Safe, Hateful, Spam).
- **Automated Grading**: Uses a "Judge" LLM (GPT-4o) to evaluate the agent's performance based on professionalism and policy adherence.
- **Regression Testing**: Ensures that changes to prompts or tools don't degrade the quality of previous "passing" cases.

### 5. Choice of Tools (PostgreSQL & SMTP)
- **PostgreSQL**: Industry standard for reliability. It serves as both our application state and our LangGraph checkpointer, providing a unified source of truth.
- **Email/Slack**: Chosen as the "North Star" for enterprise notification. It demonstrates the ability to integrate with third-party APIs to bridge the gap between AI decisions and human actions.

### 5. Trade-offs & Future Improvements
- **Trade-off (Cost vs. Speed)**: We currently use `gpt-3.5-turbo` for cost-efficiency. In a high-stakes production environment, a transition to `gpt-4o` would improve reasoning accuracy at a higher cost.
- **Future Improvement**: Implementing a **Redis Cache** for frequently seen postcard text would drastically reduce LLM costs and latency.
- **Future Improvement**: Adding a **Message Queue (Celery/RabbitMQ)** for the "Take Action" step to ensure 100% delivery reliability even during downstream service outages.
