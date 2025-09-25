"""
State Manager Service

Redis-based shared state management for document processing pipeline.
Provides shared state between FastAPI and Celery workers.
"""

import json
import redis
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class RedisStateManager:
    """Manages shared state using Redis for cross-process communication"""
    
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379, db: int = 0):
        """Initialize Redis connection for state management"""
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=db,
            decode_responses=True
        )
        self.webhook_prefix = "webhook:"
        self.job_state_prefix = "job:"
        self.document_prefix = "doc:"
        
    def ping(self) -> bool:
        """Check Redis connectivity"""
        try:
            return self.redis_client.ping()
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            return False
    
    # Document Metadata Management
    
    def set_document_metadata(self, document_id: str, metadata: Dict[str, Any], ttl: int = 86400) -> bool:
        """Store document metadata with TTL (default 24 hours)"""
        try:
            key = f"{self.document_prefix}{document_id}"
            self.redis_client.setex(
                key,
                ttl,
                json.dumps(metadata, default=str)
            )
            return True
        except Exception as e:
            logger.error(f"Failed to set document metadata: {e}")
            return False
    
    def get_document_metadata(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve document metadata"""
        try:
            key = f"{self.document_prefix}{document_id}"
            data = self.redis_client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get document metadata: {e}")
            return None
    
    def update_document_status(self, document_id: str, status: str) -> bool:
        """Update document processing status"""
        metadata = self.get_document_metadata(document_id)
        if metadata:
            metadata["status"] = status
            metadata["updated_at"] = datetime.utcnow().isoformat()
            return self.set_document_metadata(document_id, metadata)
        return False
    
    # Job State Management
    
    def set_job_state(self, job_id: str, state: Dict[str, Any], ttl: int = 3600) -> bool:
        """Store job pipeline state with TTL (default 1 hour)"""
        try:
            key = f"{self.job_state_prefix}{job_id}"
            self.redis_client.setex(
                key,
                ttl,
                json.dumps(state, default=str)
            )
            return True
        except Exception as e:
            logger.error(f"Failed to set job state: {e}")
            return False
    
    def get_job_state(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve job pipeline state"""
        try:
            key = f"{self.job_state_prefix}{job_id}"
            data = self.redis_client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get job state: {e}")
            return None
    
    # Webhook Management
    
    def register_webhook(self, webhook_id: str, webhook_data: Dict[str, Any]) -> bool:
        """Register a new webhook"""
        try:
            key = f"{self.webhook_prefix}{webhook_id}"
            # Store webhook permanently (no TTL)
            self.redis_client.set(key, json.dumps(webhook_data, default=str))
            # Add to webhook index
            self.redis_client.sadd("webhooks:index", webhook_id)
            return True
        except Exception as e:
            logger.error(f"Failed to register webhook: {e}")
            return False
    
    def get_webhook(self, webhook_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve webhook by ID"""
        try:
            key = f"{self.webhook_prefix}{webhook_id}"
            data = self.redis_client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get webhook: {e}")
            return None
    
    def list_webhooks(self, active_only: bool = False) -> List[Dict[str, Any]]:
        """List all webhooks, optionally filtering by active status"""
        try:
            webhook_ids = self.redis_client.smembers("webhooks:index")
            webhooks = []
            for webhook_id in webhook_ids:
                webhook = self.get_webhook(webhook_id)
                if webhook:
                    if not active_only or webhook.get("active", False):
                        webhooks.append(webhook)
            return webhooks
        except Exception as e:
            logger.error(f"Failed to list webhooks: {e}")
            return []
    
    def update_webhook(self, webhook_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing webhook"""
        webhook = self.get_webhook(webhook_id)
        if webhook:
            webhook.update(updates)
            webhook["updated_at"] = datetime.utcnow().isoformat()
            return self.register_webhook(webhook_id, webhook)
        return False
    
    def delete_webhook(self, webhook_id: str) -> bool:
        """Delete a webhook"""
        try:
            key = f"{self.webhook_prefix}{webhook_id}"
            self.redis_client.delete(key)
            self.redis_client.srem("webhooks:index", webhook_id)
            return True
        except Exception as e:
            logger.error(f"Failed to delete webhook: {e}")
            return False
    
    # Celery Task Result Storage
    
    def store_task_result(self, job_id: str, result: Dict[str, Any]) -> bool:
        """Store Celery task processing result"""
        try:
            # Store result
            key = f"result:{job_id}"
            self.redis_client.setex(
                key,
                3600,  # 1 hour TTL
                json.dumps(result, default=str)
            )
            
            # Update job state if exists
            if result.get("status") == "completed":
                state = {
                    "stage": "completed",
                    "completed_at": datetime.utcnow().isoformat(),
                    "agent_results": result.get("agent_results", {})
                }
                self.set_job_state(job_id, state)
            
            return True
        except Exception as e:
            logger.error(f"Failed to store task result: {e}")
            return False
    
    def get_task_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve Celery task processing result"""
        try:
            key = f"result:{job_id}"
            data = self.redis_client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get task result: {e}")
            return None


# Singleton instance for easy import
_state_manager: Optional[RedisStateManager] = None


def get_state_manager(redis_host: str = "localhost", redis_port: int = 6379, db: int = 0) -> RedisStateManager:
    """Get or create singleton state manager instance"""
    global _state_manager
    if _state_manager is None:
        _state_manager = RedisStateManager(redis_host, redis_port, db)
    return _state_manager