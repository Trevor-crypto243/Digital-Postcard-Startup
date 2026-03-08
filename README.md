# Digital Postcard Automation Pipeline (Agentic V2)

This repository contains an advanced Agentic Systems Postcard Content QA pipeline, demonstrating production-level reliability, asynchronous orchestration with LangGraph, and Human-in-the-Loop (HITL) capabilities.

---

## 💡 Why This Pipeline?
Low-stakes AI (chatbots) can afford to be purely probabilistic. However, **enterprise-grade automation** (like Postcard Content QA) requires a **Deterministic AI Pipeline**. This project was built to solve the "unpredictability" problem of LLMs by:
1.  **Guarding Profits**: Preventing costly printing of policy-violating or invalid postcards.
2.  **Risk Mitigation**: Ensuring hateful or fraudulent content never reaches a customer.
3.  **Human Efficiency**: Automating 90% of binary decisions while routing only the most ambiguous 10% to human experts.

---

## 🛠️ Features & Engineering Standards
- **Agentic Orchestration**: Uses **LangGraph** for non-linear, stateful reasoning, allowing for complex retry loops and conditional routing.
- **Production Resilience**: Implements node-level error handling, exponential backoff, and non-blocking asynchronous execution.
- **Tool Integration**: Agent dynamically uses Slack and Email tools for operational routing and user notifications.
- **Memory Persistence**: Uses **PostgreSQL** to track the "order journey" (checkpointing), ensuring no state is lost during system restarts.
- **Human-in-the-Loop**: Integrated Streamlit dashboard for manual review, providing the **Final Authority** on ambiguous content.

---

## 🏗️ Architectural Decisions & Trade-offs

### 1. Why LangGraph over LangChain-only or AutoGPT?
- **Deterministic Control**: Traditional "Agent" frameworks often suffer from "infinite loops" or unpredictable tool usage. LangGraph allows us to define a strict state machine where transitions (e.g., Validation -> LLM -> Action) are governed by code, not just prompts.
- **Auditability**: Every transition in the graph is a checkpoint in PostgreSQL. We can "time-travel" to see exactly why an agent made a specific decision at a specific node.
- **Safe Tool Execution**: Tools like `send_slack_alert` are not called directly by the LLM in a "Cowboy" fashion. They are orchestrated within specific nodes that have access to validated system state.

### 2. Asynchronous vs. Synchronous
- **Trade-off**: `async` code is slightly more complex to write/debug.
- **Decision**: We chose a 100% non-blocking architecture (FastAPI + Async Python) because high-volume postcard processing shouldn't stall on a slow OpenAI response. This allows the system to scale horizontally with minimal CPU overhead.

---

## 🛡️ Security, Risk Mitigation & Edge Cases

### 1. Edge Case Handling
- **Prompt Injection**: Mitigated by strict Pydantic schema enforcement. The agent's output *must* conform to a boolean/enum result; it cannot simply "tell the system to do something else."
- **PII Leakage**: The pipeline includes a deterministic validation step that checks for obvious sensitive patterns before the content is sent to an external LLM.
- **Rate Limit Exhaustion (HTTP 429)**: Mitigated by **Exponential Backoff** (node-level) and a **Graceful Fallback** to the Human review queue. The system never returns a 500; it simply alerts a moderator.

### 2. Safe Tool Execution & Final Authority
- **No "Ghost" Emails**: The `send_email_to_user` tool is only invoked on a `REJECTED` status. If the model is uncertain, it is *forced* to route to the HITL app.
- **Human Supremacy**: The Streamlit interface acts as the **Final Authority**. A human decision in the `human_reviews` table overrides any previous AI classification, ensuring that the "Brand Voice" is always protected.

---

## 📊 Observability & Operational Risks

### 1. What is Observed?
- **Token Utilization**: Each request tracks its token count to monitor the cost per postcard.
- **Classification Accuracy**: By comparing AI decisions against the `human_reviews` audit log, we calculate a **Precision/Recall** metric for the agent.
- **Latency**: We monitor node-level timing to identify bottlenecks in the reasoning process.

### 2. Economic Risks
- **Cost Runaway**: Mitigated by setting strict `max_retries` on AI nodes. If a decision isn't reached in 3 attempts, it is flagged for a human to prevent burning tokens on recursive reasoning.

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.11+**
- **Docker & Docker Compose**
- **OpenAI API Key**

### 2. Installation & Run
```bash
# Setup Environment
make install
cp .env.example .env

# Launch Infrastructure (API + DB)
make up

# Run HITL Dashboard
make run-hitl
```

---

## 🧪 Testing
```bash
# Integration Tests
python3 tests/verify_full_functionality.py

# LLM-as-a-Judge Eval Suite
PYTHONPATH=. python3 tests/eval_suite.py
```

---

## 📂 Repository Structure
- `/src/agent`: LangGraph state machine and resilient LLM nodes.
- `/src/engine`: Workflow orchestration and pipeline logic.
- `/src/api`: FastAPI routes and security middleware.
- `/scripts`: Demo seeding and utility scripts.
