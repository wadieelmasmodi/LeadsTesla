"""Notification module for sending leads to n8n webhook."""
from typing import Dict
import logging
import requests
from config import N8N_WEBHOOK_URL

class NotificationError(Exception):
    """Raised when notification fails."""
    pass

def post_to_n8n(payload: Dict, logger: logging.Logger) -> None:
    """Post lead data to n8n webhook.
    
    Args:
        payload: Lead data to send
        logger: Logger instance for recording results
        
    Raises:
        NotificationError: If webhook call fails
    """
    if not N8N_WEBHOOK_URL:
        raise NotificationError("N8N_WEBHOOK_URL environment variable not set")
        
    try:
        response = requests.post(
            N8N_WEBHOOK_URL,
            json=payload,
            timeout=10
        )
        
        if response.status_code >= 300:
            logger.warning(
                f"Webhook returned non-success status {response.status_code}: {response.text}"
            )
        else:
            logger.info(f"Lead {payload['key']} sent successfully to webhook")
            
    except Exception as e:
        raise NotificationError(f"Failed to send lead {payload['key']}: {str(e)}")