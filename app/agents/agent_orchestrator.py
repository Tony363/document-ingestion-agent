"""
Agent Orchestrator

Coordinates the execution of multiple agents in the document processing pipeline.
Manages state transitions, error handling, and pipeline flow control.
"""

from typing import Dict, List, Any, Optional
from enum import Enum
import asyncio
import logging
from datetime import datetime
from pydantic import BaseModel, Field

from .base_agent import BaseAgent, AgentContext, AgentResult, AgentStatus
from .classification_agent import ClassificationInput
from .mistral_ocr_agent import OCRInput
from .content_analysis_agent import AnalysisInput
from .schema_generation_agent import SchemaInput
from .validation_agent import ValidationInput

class PipelineStage(str, Enum):
    """Pipeline execution stages"""
    RECEIVED = "received"
    CLASSIFICATION = "classification"
    OCR = "ocr"
    ANALYSIS = "analysis"
    SCHEMA_GENERATION = "schema_generation"
    VALIDATION = "validation"
    COMPLETED = "completed"
    FAILED = "failed"

class PipelineState(BaseModel):
    """Pipeline execution state"""
    stage: PipelineStage
    job_id: str
    document_id: str
    started_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    agent_results: Dict[str, AgentResult] = Field(default_factory=dict)
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DocumentData(BaseModel):
    """Document data passed through the pipeline"""
    file_path: str
    mime_type: str
    file_size: int
    content_hash: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AgentOrchestrator:
    """
    Orchestrates agent execution in the document processing pipeline
    """
    
    def __init__(self):
        self.logger = logging.getLogger("orchestrator")
        self.agents: Dict[str, BaseAgent] = {}
        self.pipeline_states: Dict[str, PipelineState] = {}
        
    def register_agent(self, stage: str, agent: BaseAgent):
        """
        Register an agent for a specific pipeline stage
        
        Args:
            stage: Pipeline stage name
            agent: Agent instance
        """
        self.agents[stage] = agent
        self.logger.info(f"Registered agent {agent.name} for stage {stage}")
        
    async def execute_pipeline(
        self,
        document: DocumentData,
        context: AgentContext
    ) -> PipelineState:
        """
        Execute the complete document processing pipeline
        
        Args:
            document: Document data to process
            context: Agent execution context
            
        Returns:
            Final pipeline state with all results
        """
        # Initialize pipeline state
        state = PipelineState(
            stage=PipelineStage.RECEIVED,
            job_id=context.job_id,
            document_id=context.document_id,
            started_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.pipeline_states[context.job_id] = state
        
        try:
            # Stage 1: Document Classification
            state.stage = PipelineStage.CLASSIFICATION
            state.updated_at = datetime.utcnow()
            
            if "classification" in self.agents:
                classification_result = await self.agents["classification"].execute(
                    document, context
                )
                state.agent_results["classification"] = classification_result
                
                if classification_result.status == AgentStatus.FAILED:
                    raise Exception(f"Classification failed: {classification_result.error}")
            
            # Stage 2: OCR Processing
            state.stage = PipelineStage.OCR
            state.updated_at = datetime.utcnow()
            
            if "ocr" in self.agents:
                ocr_input = OCRInput(
                    file_path=document.file_path,
                    mime_type=document.mime_type,
                    document_type=state.agent_results["classification"].data.document_type if state.agent_results.get("classification") and state.agent_results["classification"].data else "unknown"
                )
                
                ocr_result = await self.agents["ocr"].execute(
                    ocr_input, context
                )
                state.agent_results["ocr"] = ocr_result
                
                if ocr_result.status == AgentStatus.FAILED:
                    raise Exception(f"OCR failed: {ocr_result.error}")
            
            # Stage 3: Content Analysis
            state.stage = PipelineStage.ANALYSIS
            state.updated_at = datetime.utcnow()
            
            if "analysis" in self.agents:
                analysis_input = AnalysisInput(
                    extracted_text=state.agent_results["ocr"].data.full_text if state.agent_results.get("ocr") and state.agent_results["ocr"].data else "",
                    document_type=state.agent_results["classification"].data.document_type if state.agent_results.get("classification") and state.agent_results["classification"].data else "unknown"
                )
                
                analysis_result = await self.agents["analysis"].execute(
                    analysis_input, context
                )
                state.agent_results["analysis"] = analysis_result
                
                if analysis_result.status == AgentStatus.FAILED:
                    raise Exception(f"Analysis failed: {analysis_result.error}")
            
            # Stage 4: Schema Generation
            state.stage = PipelineStage.SCHEMA_GENERATION
            state.updated_at = datetime.utcnow()
            
            if "schema" in self.agents:
                schema_input = SchemaInput(
                    document_type=state.agent_results["classification"].data.document_type if state.agent_results.get("classification") and state.agent_results["classification"].data else "unknown",
                    extracted_data=state.agent_results["analysis"].data.dict() if state.agent_results.get("analysis") and state.agent_results["analysis"].data else {}
                )
                
                schema_result = await self.agents["schema"].execute(
                    schema_input, context
                )
                state.agent_results["schema"] = schema_result
                
                if schema_result.status == AgentStatus.FAILED:
                    raise Exception(f"Schema generation failed: {schema_result.error}")
            
            # Stage 5: Validation
            state.stage = PipelineStage.VALIDATION
            state.updated_at = datetime.utcnow()
            
            if "validation" in self.agents:
                validation_input = ValidationInput(
                    schema=state.agent_results["schema"].data.dict() if state.agent_results.get("schema") and state.agent_results["schema"].data else {},
                    document_type=state.agent_results["classification"].data.document_type if state.agent_results.get("classification") and state.agent_results["classification"].data else "unknown"
                )
                
                validation_result = await self.agents["validation"].execute(
                    validation_input, context
                )
                state.agent_results["validation"] = validation_result
                
                if validation_result.status == AgentStatus.FAILED:
                    raise Exception(f"Validation failed: {validation_result.error}")
            
            # Pipeline completed successfully
            state.stage = PipelineStage.COMPLETED
            state.completed_at = datetime.utcnow()
            state.updated_at = datetime.utcnow()
            
            self.logger.info(f"Pipeline completed for job {context.job_id}")
            
        except Exception as e:
            # Pipeline failed
            state.stage = PipelineStage.FAILED
            state.error = str(e)
            state.updated_at = datetime.utcnow()
            
            self.logger.error(f"Pipeline failed for job {context.job_id}: {e}")
            
        finally:
            self.pipeline_states[context.job_id] = state
            
        return state
    
    async def execute_parallel_stages(
        self,
        stages: List[str],
        context: AgentContext
    ) -> Dict[str, AgentResult]:
        """
        Execute multiple pipeline stages in parallel
        
        Args:
            stages: List of stage names to execute
            context: Agent execution context
            
        Returns:
            Dictionary of stage results
        """
        tasks = []
        stage_names = []
        
        for stage in stages:
            if stage in self.agents:
                tasks.append(self.agents[stage].execute({}, context))
                stage_names.append(stage)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            stage: result if not isinstance(result, Exception) else None
            for stage, result in zip(stage_names, results)
        }
    
    def get_pipeline_state(self, job_id: str) -> Optional[PipelineState]:
        """
        Get current pipeline state for a job
        
        Args:
            job_id: Job identifier
            
        Returns:
            Pipeline state or None if not found
        """
        return self.pipeline_states.get(job_id)
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all registered agents
        
        Returns:
            Health status of all agents
        """
        health_status = {
            "orchestrator": "healthy",
            "agents": {}
        }
        
        for stage, agent in self.agents.items():
            try:
                health_status["agents"][stage] = await agent.health_check()
            except Exception as e:
                health_status["agents"][stage] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        return health_status