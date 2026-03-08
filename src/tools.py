from langchain_core.tools import tool
from src.logger import get_logger
from typing import Optional

logger = get_logger("agent_tools")

@tool
def send_slack_alert(channel: str, message: str, severity: str = "info") -> str:
    """
    Use this tool to send critical operational alerts or incident triage messages to the internal company Slack #channel.
    Only use this for system errors, or when immediate moderation attention is required for hateful content.
    """
    logger.warning(f"[SLACK ALERT - {severity.upper()}] to {channel}: {message}")
    # Mocked Integration: In production this would use slack_sdk to post to a webhook
    return f"Successfully routed alert to Slack channel {channel}."

@tool
def send_email_to_user(user_id: str, subject: str, body: str) -> str:
    """
    Use this tool to send automated emails directly to users regarding their postcard submissions.
    Use this when content is rejected due to policy violations, or to inform them of corrections.
    """
    logger.info(f"[EMAIL DISPATCH] To: {user_id} | Subject: {subject} | Body: {body}")
    # Mocked Integration: In production this would hit SendGrid/AWS SES APIs
    return f"Email queued for delivery to user {user_id}."
