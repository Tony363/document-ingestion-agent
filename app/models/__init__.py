"""Models package for Document Ingestion Agent"""

from .webhook_models import (
    WebhookRegistration,
    WebhookUpdate,
    WebhookResponse,
    WebhookPayload
)

__all__ = [
    "WebhookRegistration",
    "WebhookUpdate",
    "WebhookResponse",
    "WebhookPayload"
]