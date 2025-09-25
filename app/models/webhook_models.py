"""
Webhook Models

Pydantic models for webhook request and response handling.
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime


class WebhookRegistration(BaseModel):
    """Model for webhook registration request"""
    webhook_url: HttpUrl = Field(..., description="URL to receive webhook callbacks")
    webhook_name: str = Field(..., description="Friendly name for the webhook")
    events: Optional[List[str]] = Field(
        default=["document.processed"],
        description="Events to subscribe to"
    )


class WebhookUpdate(BaseModel):
    """Model for webhook update request"""
    webhook_url: Optional[HttpUrl] = Field(None, description="New webhook URL")
    webhook_name: Optional[str] = Field(None, description="New webhook name")
    active: Optional[bool] = Field(None, description="Enable/disable webhook")
    events: Optional[List[str]] = Field(None, description="Updated event subscriptions")


class WebhookResponse(BaseModel):
    """Model for webhook response"""
    id: str
    name: str
    url: str
    events: List[str]
    created_at: str
    updated_at: Optional[str] = None
    active: bool


class WebhookPayload(BaseModel):
    """Model for webhook delivery payload"""
    event: str
    timestamp: str
    document_id: str
    job_id: str
    document_schema: Optional[Dict[str, Any]] = Field(None, alias="schema")
    error: Optional[str] = None