# Digital Postcard Automation Pipeline (Agentic V2)

This repository contains an advanced Agentic Systems Postcard Content QA pipeline, demonstrating production-level reliability, asynchronous orchestration with LangGraph, and Human-in-the-Loop (HITL) capabilities.

---

## 📈 Business Case & Assumptions (Write-up)

**Workflow Chosen**: Postcard Content QA (Operations Pillar)

**The Problem**: Our digital postcard startup currently processes ~5,000 submissions daily. Each postcard is manually reviewed for "Brand Safety" (hate speech, PII, or nonsensical gibberish), costing $0.15 per review in labor and causing a 4-hour delay in delivery.

**The Solution**: This Agentic Pipeline automates the classification and routing of postcards.
- **Goal Metric**: 90% reduction in manual review volume and 85% reduction in "Time-to-Print" latency.
- **Assumptions (Baseline)**: 
    - 85% of postcards are clearly safe (Auto-Approved).
    - 5% are clearly violations (Auto-Rejected).
    - 10% are ambiguous/creative (Routed to HITL Dashboard).
- **Impact Logic**: By automating 90% of decisions, we save **$675/day** in operational costs and ensure "Safe" postcards are ready for printing in seconds, not hours.

---

## 🏗️ Deep Dive: Architecture & Design
For a technical breakdown of the system's state machine, failure handling, and the "System that Builds Systems" pattern, see the [Architecture Overview](architecture_overview.md).

---

## 🛠️ Features & Engineering Standards
- **Agentic Orchestration**: Uses **LangGraph** for non-linear, stateful reasoning, allowing for complex retry loops and conditional routing.
- **Production Resilience**: Implements node-level error handling, exponential backoff, and non-blocking asynchronous execution.
- **Operational Integrations**: 
    - **Slack**: Real-time incident triage and moderation alerts via Webhooks.
    - **Email**: Automated user notifications for rejections and policy updates.
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

### **A. End-to-End Automated Test Suite**
```bash
# Integration Tests
python3 tests/verify_full_functionality.py

# LLM-as-a-Judge Eval Suite
PYTHONPATH=. python3 tests/eval_suite.py
```

### **B. Manual Testing (cURL)**
The API uses an authenticated header: `X-Agentic-API-Key: agentic-demo-key-123`.

**Evaluate a Postcard:**
```bash
curl -X POST "http://localhost:8000/api/v1/postcards/evaluate" \
     -H "Content-Type: application/json" \
     -H "X-Agentic-API-Key: agentic-demo-key-123" \
     -d '{
       "id": "pc-888", 
       "user_id": "u-123", 
       "text_content": "This is a beautiful test postcard!"
     }'
```

---

## 🏗️ Database Optimization & Scalability

The persistence layer is designed for enterprise-grade reliability and performance:

- **Stateful Persistence (LangGraph)**: Every "reasoning journey" is saved as a binary checkpoint in PostgreSQL. This allows the system to recover from crashes mid-execution and provides a complete audit trail of the agent's logic.
- **Scalable Indexing**: The `checkpoints` and `human_reviews` tables are indexed for high-concurrency retrieval. As the system scales to millions of postcards, lookups for specific `thread_id`s remain $O(1)$ to $O(\log n)$.
- **Security & Integrity**: 
    - **Lease-Based Locking**: LangGraph uses PostgreSQL to ensure that only one worker can process a specific `thread_id` at a time, preventing race conditions in distributed environments.
    - **ACID Compliance**: Every human resolution and AI decision is committed within a transaction, ensuring that the "Brand Safety" audit log is never corrupted.
- **Efficient I/O**: We use `AsyncPostgresSaver` with a connection pool, allowing the system to handle thousands of concurrent DB operations without exhausting system resources.

---

## 📋 Requirement Traceability (Interview Dashboard)

This project explicitly satisfies all 6 core requirements and the "system that builds systems" mandatory criteria:

| Requirement | Implementation Detail | Location |
| :--- | :--- | :--- |
| **1. Accept Input** | FastAPI REST Endpoint (`POST /evaluate`) | `src/api/routes.py` |
| **2. Purposeful LLM Step** | Agentic Reasoning & Policy Evaluation | `src/agent/llm_step.py` |
| **3. Deterministic Step** | Content length & regex validation | `src/engine/pipeline.py` |
| **4. Automated Action** | Slack Alerts, Email Dispatch, DB Persistence | `src/agent/tools.py` |
| **5. Failure Handling** | Exponential Backoff + Fallback to Human Review | `src/agent/llm_step.py` |
| **6. Output Validation** | Pydantic Schema Enforcement (Structured Outputs) | `src/models/schemas.py` |

### 🏗️ "System that Builds Systems" (Reusability)
The project is built on a **Workflow Runner** pattern. 
- **Reusable Core**: `src/engine/config_runner.py` provides a generic `WorkflowRunner` that accepts any sequence of async/sync steps.
- **Scalability**: Adding a new business workflow (e.g., "Email Receipt QA") takes **<15 minutes** by simply defining new step functions and composing them in a new runner instance.

---

## 📂 Repository Structure
- `/src/agent`: LangGraph state machine, resilient LLM nodes, and operational tools.
- `/src/engine`: The **Workflow Runner** core and specific pipeline steps.
- `/src/api`: FastAPI entrypoints and security layer.
- `/infra`: Docker, Database initializers (`init.sql`), and environment templates.
- `/scripts`: Demo seeding and utility scripts.
