import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from src.models.schemas import PostcardEvaluation, QAStatus
from src.utils.reliability import with_retry
from src.utils.logger import get_logger

logger = get_logger("llm_step")

SYSTEM_PROMPT = """You are a helpful and strict content moderation assistant for a digital postcard startup.
Your job is to read the text of a postcard and evaluate it based on the following rules:

1. REJECT if the text contains profanity, hate speech, explicit content, or spam.
2. REJECT if the text is entirely nonsensical gibberish.
3. NEEDS_REVIEW if the text is borderline, contains ambiguous phrasing that might be inappropriate, or has excessive typos.
4. APPROVED if the text is a normal, friendly, or benign message suitable for a postcard.

Analyze the given text carefully and provide your reasoning. If there are minor typos or issues, you may supply suggested_corrections.

Return the result purely in structured JSON matching the requested schema.
"""

prompt_template = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("user", "Evaluate the following postcard text:\n\n{text_content}")
])

# Initialize the LLM with structured output matching our Pydantic model
try:
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.1)
    structured_llm = llm.with_structured_output(PostcardEvaluation)
    evaluation_chain = prompt_template | structured_llm
except Exception as e:
    logger.warning(f"Could not initialize OpenAI LLM: {e}. Ensure OPENAI_API_KEY is set in .env")
    evaluation_chain = None


async def evaluate_postcard_text(text_content: str) -> PostcardEvaluation:
    """Evaluates postcard text with LLM and retries on failure."""
    if not evaluation_chain:
         logger.error("LLM Chain not initialized. Cannot evaluate text.")
         # Fallback to NEEDS_REVIEW if LLM is unavailable
         return PostcardEvaluation(
             status=QAStatus.NEEDS_REVIEW,
             reasoning="System Error: LLM unavailable, manual review required.",
             suggested_corrections=None
         )
         
    async def invoke_llm():
        logger.debug(f"Invoking LLM for text analysis...")
        # Since we use ChatOpenAI natively sync here, we use ainvoke if supported by the chain
        result = await evaluation_chain.ainvoke({"text_content": text_content})
        return result

    try:
        # We wrap the LLM call with our custom async retry logic from the boilerplate
        evaluation = await with_retry(invoke_llm, max_retries=3, delay=1.0)
        logger.info(f"LLM Classification complete: {evaluation.status}")
        return evaluation
    except Exception as e:
        logger.error(f"LLM evaluation failed after retries: {e}")
        # Control Gate: Graceful fallback if structured parsing or LLM totally fails
        return PostcardEvaluation(
             status=QAStatus.NEEDS_REVIEW,
             reasoning="Automated moderation failed due to technical error.",
             suggested_corrections=None
         )
