# Digital Postcard Automation Write-up

### What I Built
I implemented an automated Postcard Content QA pipeline exposed via a FastAPI endpoint. The pipeline uses a custom `WorkflowRunner` (satisfying the "system that builds systems" requirement) to execute sequential steps: a deterministic pre-validation guardrail, an LLM classification step leveraging LangChain, and a mock action execution step.

### Why I Chose this Workflow (Impact Logic)
I chose the **Operations: Postcard Content QA** workflow. Reviewing user-submitted content is a tedious, low-value task for human agents. The goal metric is **time saved / error reduction**. By applying a smart routing layer with LLMs:
1. ~80% of benign postcards are automatically approved, freeing operational bandwidth.
2. Inappropriate content is rejected instantly to maintain platform safety.
3. Only ambiguous or complex cases are routed to human agents.

### Assumptions
- Approximately 15% of submissions have typos or concerning content requiring review.
- Human review takes an average of 30 seconds per postcard; standardizing this workflow scales operations significantly.
- OpenAI GPT-3.5-turbo (cheap and fast) is sufficient for initial text classification accuracy compared to larger models.

### Fault Tolerance & Failure Modes
I intentionally handled the "LLM Service Unavailable / Bad Output Schema" failure mode. LLMs can occasionally return unparseable text or rate-limit timeouts.
To mitigate this:
1. I wrapped the LangChain call using a deterministic Pydantic schema extractor.
2. I implemented an exponential backoff retry mechanism (`with_retry`).
3. **Control Gate:** If the LLM call entirely fails or returns garbage even after retries, an exception block catches the error and safely falls back to returning a `NEEDS_REVIEW` status. This guarantees the pipeline never crashes mid-flow and ensures a human reviews any postcard the AI couldn't confidently classify.
