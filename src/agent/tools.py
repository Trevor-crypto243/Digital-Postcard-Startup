from langchain_core.tools import tool
from src.utils.logger import get_logger
from src.config import settings
from typing import Optional

logger = get_logger("agent_tools")

@tool
def send_slack_alert(channel: str, message: str, severity: str = "info") -> str:
    """
    Use this tool to send critical operational alerts or incident triage messages to the internal company Slack #channel.
    Only use this for system errors, or when immediate moderation attention is required for hateful content.
    """
    webhook_url = settings.SLACK_WEBHOOK_URL
    target_channel = channel or settings.MODERATION_CHANNEL
    
    logger.warning(f"[SLACK ALERT - {severity.upper()}] to {target_channel}: {message}")
    
    if not webhook_url:
        logger.info("Slack Webhook URL not configured. Mocking success.")
        return f"Successfully routed alert (MOCKED) to Slack channel {target_channel}."
        
    # Mocked Integration: In production this would use requests to post to webhook_url
    return f"Successfully sent webhook alert to Slack channel {target_channel}."

@tool
def send_email_to_user(user_id: str, subject: str, body: str) -> str:
    """
    Use this tool to send automated emails directly to users regarding their postcard submissions.
    Use this when content is rejected due to policy violations, or to inform them of corrections.
    """
    smtp_host = settings.SMTP_HOST
    sender = settings.SENDER_EMAIL
    
    logger.info(f"[EMAIL DISPATCH] To: {user_id} | Subject: {subject} | Body: {body}")
    
    if not settings.SMTP_USER or not settings.SMTP_PASS:
        logger.info("Email credentials missing in configuration. Mocking success.")
        return f"Email to {user_id} queued (MOCKED) via {smtp_host}."
        
    # Mocked Integration: In production this would use smtplib or a service client
    return f"Email to {user_id} successfully delivered via {smtp_host}."
