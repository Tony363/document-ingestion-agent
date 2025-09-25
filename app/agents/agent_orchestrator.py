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
        
    def _get_document_type(self, state: PipelineState) -> str:
        """
        Safely extract document type from classification results
        
        Args:
            state: Current pipeline state
            
        Returns:
            Document type or "unknown" if not available
        """
        classification_result = state.agent_results.get("classification")
        if classification_result and classification_result.data:
            if hasattr(classification_result.data, 'document_type'):
                return classification_result.data.document_type
        return "unknown"
    
    def _get_ocr_text(self, state: PipelineState) -> str:
        """
        Safely extract OCR text from results
        
        Args:
            state: Current pipeline state
            
        Returns:
            Extracted text or empty string if not available
        """
        ocr_result = state.agent_results.get("ocr")
        if ocr_result and ocr_result.data:
            if hasattr(ocr_result.data, 'full_text'):
                return ocr_result.data.full_text
        return ""
    
    def _get_analysis_data(self, state: PipelineState) -> Dict[str, Any]:
        """
        Safely extract analysis data from results
        
        Args:
            state: Current pipeline state
            
        Returns:
            Analysis data dictionary or empty dict if not available
        """
        analysis_result = state.agent_results.get("analysis")
        if analysis_result and analysis_result.data:
            if hasattr(analysis_result.data, 'dict'):
                return analysis_result.data.dict()
        return {}
    
    def _get_schema_data(self, state: PipelineState) -> Dict[str, Any]:
        """
        Safely extract schema data from results
        
        Args:
            state: Current pipeline state
            
        Returns:
            Schema data dictionary or empty dict if not available
        """
        schema_result = state.agent_results.get("schema")
        if schema_result and schema_result.data:
            if hasattr(schema_result.data, 'dict'):
                return schema_result.data.dict()
        return {}
        
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
                # Safely get document type from classification results
                document_type = self._get_document_type(state)
                
                ocr_input = OCRInput(
                    file_path=document.file_path,
                    mime_type=document.mime_type,
                    document_type=document_type
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
                # Safely get OCR text and document type
                extracted_text = self._get_ocr_text(state)
                document_type = self._get_document_type(state)
                
                analysis_input = AnalysisInput(
                    extracted_text=extracted_text,
                    document_type=document_type
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
                # Safely get document type and analysis data
                document_type = self._get_document_type(state)
                extracted_data = self._get_analysis_data(state)
                
                schema_input = SchemaInput(
                    document_type=document_type,
                    extracted_data=extracted_data
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
                # Safely get schema data and document type
                schema_data = self._get_schema_data(state)
                document_type = self._get_document_type(state)
                
                validation_input = ValidationInput(
                    schema=schema_data,
                    document_type=document_type
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
        inputs: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, AgentResult]:
        """
        Execute multiple pipeline stages in parallel
        
        Args:
            stages: List of stage names to execute
            inputs: Dictionary of inputs for each stage
            context: Agent execution context
            
        Returns:
            Dictionary of stage results
        """
        tasks = []
        stage_names = []
        
        for stage in stages:
            if stage in self.agents:
                # Use provided input for stage or empty dict if not provided
                stage_input = inputs.get(stage, {})
                tasks.append(self.agents[stage].execute(stage_input, context))
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