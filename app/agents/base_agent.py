"""
Base agent class for the agentic processing system
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Base class for all processing agents"""
    
    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.status = "initialized"
        self.created_at = datetime.utcnow()
        self.metrics = {
            "processed_count": 0,
            "success_count": 0,
            "error_count": 0,
            "average_processing_time": 0.0
        }
        
    @abstractmethod
    async def process(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process document data and return results
        
        Args:
            document_data: Dictionary containing document information and content
            
        Returns:
            Dictionary with processing results
        """
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status and metrics"""
        return {
            "name": self.name,
            "version": self.version,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "metrics": self.metrics
        }
    
    async def validate_input(self, document_data: Dict[str, Any]) -> bool:
        """Validate input data before processing"""
        required_fields = ["document_id", "content"]
        
        for field in required_fields:
            if field not in document_data:
                logger.error(f"Missing required field in {self.name}: {field}")
                return False
                
        return True
    
    def update_metrics(self, success: bool, processing_time: float):
        """Update agent processing metrics"""
        self.metrics["processed_count"] += 1
        
        if success:
            self.metrics["success_count"] += 1
        else:
            self.metrics["error_count"] += 1
            
        # Update rolling average of processing time
        total_time = self.metrics["average_processing_time"] * (self.metrics["processed_count"] - 1)
        self.metrics["average_processing_time"] = (total_time + processing_time) / self.metrics["processed_count"]
    
    async def handle_error(self, error: Exception, document_id: str) -> Dict[str, Any]:
        """Handle processing errors consistently across agents"""
        logger.error(f"Error in {self.name} processing document {document_id}: {str(error)}")
        
        return {
            "success": False,
            "error": str(error),
            "agent": self.name,
            "document_id": document_id,
            "timestamp": datetime.utcnow().isoformat()
        }