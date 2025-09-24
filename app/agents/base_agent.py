"""
Base Agent Abstract Class

Provides the foundation for all document processing agents with:
- Async execution support
- Standardized logging
- Metrics collection
- Error boundaries
- Retry logic
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar, Generic
import asyncio
import time
import logging
from enum import Enum
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

T = TypeVar('T', bound=BaseModel)
R = TypeVar('R', bound=BaseModel)

class AgentStatus(str, Enum):
    """Agent execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

class AgentMetrics(BaseModel):
    """Metrics collected during agent execution"""
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[int] = None
    retry_count: int = 0
    error_count: int = 0
    confidence_score: Optional[float] = None

class AgentContext(BaseModel):
    """Shared context passed between agents"""
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    correlation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
class AgentResult(BaseModel, Generic[R]):
    """Standard result wrapper for all agents"""
    agent_name: str
    status: AgentStatus
    data: Optional[R] = None
    error: Optional[str] = None
    metrics: AgentMetrics
    context: AgentContext

class BaseAgent(ABC, Generic[T, R]):
    """
    Abstract base class for all document processing agents
    
    Type Parameters:
        T: Input data type (Pydantic model)
        R: Output data type (Pydantic model)
    """
    
    def __init__(
        self,
        name: str,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: float = 30.0
    ):
        self.name = name
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.logger = logging.getLogger(f"agent.{name}")
        
    @abstractmethod
    async def process(self, input_data: T, context: AgentContext) -> R:
        """
        Core processing logic to be implemented by each agent
        
        Args:
            input_data: Agent-specific input data
            context: Shared agent context
            
        Returns:
            Agent-specific output data
        """
        pass
    
    @abstractmethod
    async def validate_input(self, input_data: T) -> bool:
        """
        Validate input data before processing
        
        Args:
            input_data: Input data to validate
            
        Returns:
            True if input is valid, False otherwise
        """
        pass
    
    async def execute(
        self,
        input_data: T,
        context: AgentContext
    ) -> AgentResult[R]:
        """
        Execute agent with error handling and retry logic
        
        Args:
            input_data: Agent-specific input data
            context: Shared agent context
            
        Returns:
            AgentResult containing output data or error
        """
        metrics = AgentMetrics(start_time=datetime.utcnow())
        status = AgentStatus.PENDING
        result_data = None
        error = None
        
        try:
            # Validate input
            if not await self.validate_input(input_data):
                raise ValueError(f"Invalid input data for {self.name}")
            
            status = AgentStatus.RUNNING
            self.logger.info(f"Executing {self.name} for job {context.job_id}")
            
            # Execute with retries
            for attempt in range(self.max_retries):
                try:
                    # Execute with timeout
                    result_data = await asyncio.wait_for(
                        self.process(input_data, context),
                        timeout=self.timeout
                    )
                    status = AgentStatus.COMPLETED
                    break
                    
                except asyncio.TimeoutError:
                    metrics.error_count += 1
                    error = f"Timeout after {self.timeout}s"
                    self.logger.warning(f"{self.name} timeout on attempt {attempt + 1}")
                    
                except Exception as e:
                    metrics.error_count += 1
                    error = str(e)
                    self.logger.error(f"{self.name} error on attempt {attempt + 1}: {e}")
                    
                    if attempt < self.max_retries - 1:
                        status = AgentStatus.RETRYING
                        metrics.retry_count += 1
                        await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    else:
                        status = AgentStatus.FAILED
                        
        except Exception as e:
            status = AgentStatus.FAILED
            error = str(e)
            self.logger.error(f"{self.name} failed: {e}")
            
        finally:
            metrics.end_time = datetime.utcnow()
            metrics.duration_ms = int(
                (metrics.end_time - metrics.start_time).total_seconds() * 1000
            )
            
        return AgentResult(
            agent_name=self.name,
            status=status,
            data=result_data,
            error=error,
            metrics=metrics,
            context=context
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check for the agent
        
        Returns:
            Health status dictionary
        """
        return {
            "name": self.name,
            "status": "healthy",
            "max_retries": self.max_retries,
            "timeout": self.timeout
        }