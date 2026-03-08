import os
from typing import Annotated, Literal, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver

from src.models.schemas import PostcardEvaluation, QAStatus
from src.agent.tools import send_slack_alert, send_email_to_user
from src.utils.logger import get_logger
from src.config import settings

logger = get_logger("agent_graph")

# Define the State for our Graph
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    text_content: str
    evaluation: PostcardEvaluation | None
    
# System instructions detailing explicit tool usage and evaluation rules
SYSTEM_PROMPT = """You are a helpful and strict content moderation assistant for a digital postcard startup.
Your job is to read the text of a postcard and evaluate it:

1. REJECT if the text contains profanity, hate speech, explicit content, or spam.
2. REJECT if the text is entirely nonsensical gibberish.
3. NEEDS_REVIEW if the text is borderline, contains ambiguous phrasing, or has excessive typos.
4. APPROVED if the text is a normal, friendly, or benign message suitable for a postcard.

TOOLS AVALIABLE:
- If you REJECT a postcard because it is a severe policy violation (hate speech/threats), you MUST call the `send_slack_alert` tool to alert the moderation team.
- If you REJECT a postcard, you MUST call the `send_email_to_user` tool to notify them of the rejection.

Return your final structured decision using the `PostcardEvaluation` structured output ONLY after you have invoked necessary tools.
"""

tools = [send_slack_alert, send_email_to_user]

# Initialize LLM with tools and structured output capabilities
try:
    if settings.OPENAI_API_KEY:
        llm = ChatOpenAI(
            model=settings.LLM_MODEL, 
            temperature=settings.LLM_TEMPERATURE,
            openai_api_key=settings.OPENAI_API_KEY
        )
        # Add retry logic for production robustness (Exponential Backoff)
        llm_with_retry = llm.with_retry(
            stop_after_attempt=3,
            wait_exponential_jitter=True
        )
        llm_with_tools = llm_with_retry.bind_tools(tools)
        # We will use this specifically to force the structured evaluation output at the end
        eval_llm = llm_with_retry.with_structured_output(PostcardEvaluation)
    else:
        logger.warning("No OPENAI_API_KEY found in settings. Running in fallback mode.")
        llm = None
        llm_with_tools = None
        eval_llm = None
except Exception as e:
    logger.warning(f"Could not initialize OpenAI LLM: {e}")
    llm = None
    llm_with_tools = None
    eval_llm = None

# --- Graph Nodes ---
def reasoning_node(state: AgentState):
    """The agent analyzes the text and decides if it needs to use tools."""
    if not llm_with_tools:
        return {"messages": [AIMessage(content="LLM Unavailable. Routing to fallback.")]}
        
    logger.debug("Agent is reasoning about the text and potential tools...")
    # Give the agent the system prompt and the current text
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Evaluate this text: {state['text_content']}"}
    ] + state["messages"]
    
    try:
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}
    except Exception as e:
        logger.error(f"Error in reasoning_node: {e}")
        return {"messages": [AIMessage(content=f"Error during reasoning: {e}. Falling back to manual review.")]}

def finalize_evaluation_node(state: AgentState):
    """After any tools are run (or if none were needed), generate the final structured output."""
    if not eval_llm:
        # Graceful fallback control gate
        fallback = PostcardEvaluation(
            status=QAStatus.NEEDS_REVIEW,
            reasoning="System Error: LLM unavailable, manual review required.",
            suggested_corrections=None
        )
        return {"evaluation": fallback}
        
    logger.debug("Generating final structured evaluation...")
    
    # We ask the LLM to output the final struct based on the conversation history
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Text: {state['text_content']}. Provide the final structured PostcardEvaluation."}
    ] + state["messages"]
    
    try:
        struct_eval = eval_llm.invoke(messages)
        return {"evaluation": struct_eval}
    except Exception as e:
        logger.error(f"Structured Parsing failed: {e}. Fallback to NEEDS_REVIEW.")
        fallback = PostcardEvaluation(
            status=QAStatus.NEEDS_REVIEW,
            reasoning="Automated moderation failed due to technical parsing error. Handing over to Human.",
            suggested_corrections=None
        )
        return {"evaluation": fallback}

# --- Graph Edges ---
def should_continue(state: AgentState) -> Literal["tools", "finalize"]:
    """Determine if the agent called a tool or is done."""
    messages = state["messages"]
    last_message = messages[-1]
    
    # If the LLM made a tool call, route to the tools node
    if last_message.tool_calls:
        return "tools"
    # Otherwise, finalize the evaluation
    return "finalize"

# --- Build the Graph ---
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("agent", reasoning_node)
workflow.add_node("tools", ToolNode(tools))
workflow.add_node("finalize", finalize_evaluation_node)

# Add Edges
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", "finalize": "finalize"})
workflow.add_edge("tools", "agent") # Tools feedback to the agent
workflow.add_edge("finalize", END)

# DB Connection globally for the Checkpointer
DB_URI = settings.DATABASE_SYNC_URL

# Initialize connection pool for Postgres Checkpointer (Memory)
# In production, this allows 'Operational and context retention' tracing exactly what the agent did.
try:
    # Need to extract standard postgres URI from sqlalchemy format if used
    pg_uri = DB_URI.replace("postgresql+psycopg://", "postgresql://")
    pool = ConnectionPool(conninfo=pg_uri, max_size=20)
    checkpointer = PostgresSaver(pool)
    checkpointer.setup() # Ensures checkpointer tables exist
    graph_app = workflow.compile(checkpointer=checkpointer)
    logger.info("LangGraph compiled successfully WITH Postgres Memory!")
except Exception as e:
    logger.error(f"Failed to initialize Postgres checkpointer. Running in memory only mode: {e}")
    # Fallback to in-memory graph if DB is down during tests
    graph_app = workflow.compile()

async def evaluate_postcard_text(text_content: str, thread_id: str) -> PostcardEvaluation:
    """
    Entrypoint for the Postcard Pipeline.
    Notice the thread_id: Memory is like an order ID in ecommerce; 
    every step in the reasoning journey is saved to Postgres under this thread.
    """
    config = {"configurable": {"thread_id": thread_id}}
    
    # Initial state
    inputs = {
        "messages": [],
        "text_content": text_content,
        "evaluation": None
    }
    
    logger.info(f"Invoking Stateful LangGraph Agent for thread {thread_id}")
    
    # Run the graph synchronously (or async if using ainvoke/AsyncPostgresSaver)
    # Using invoke here to match standard ToolNode setup
    final_state = await graph_app.ainvoke(inputs, config=config)
    
    return final_state.get("evaluation")
