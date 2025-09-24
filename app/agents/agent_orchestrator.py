"""
Agent Orchestrator - Coordinates the agentic processing pipeline
Manages the flow of documents through all processing agents
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from .validation_agent import ValidationAgent
from .classification_agent import ClassificationAgent
from .mistral_ocr_agent import MistralOCRAgent
from .content_analysis_agent import ContentAnalysisAgent
from .schema_generation_agent import SchemaGenerationAgent

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    """Orchestrates the entire agentic processing pipeline"""
    
    def __init__(self, mistral_api_key: Optional[str] = None):
        # Initialize all agents
        self.validation_agent = ValidationAgent()
        self.classification_agent = ClassificationAgent()
        self.mistral_ocr_agent = MistralOCRAgent(api_key=mistral_api_key)
        self.content_analysis_agent = ContentAnalysisAgent()
        self.schema_generation_agent = SchemaGenerationAgent()
        
        # Processing pipeline definition
        self.pipeline_stages = [
            ("validation", self.validation_agent),
            ("classification", self.classification_agent),
            ("ocr_processing", self.mistral_ocr_agent),
            ("content_analysis", self.content_analysis_agent),
            ("schema_generation", self.schema_generation_agent)
        ]
        
        # Orchestrator metrics
        self.metrics = {
            "documents_processed": 0,
            "successful_completions": 0,
            "failed_processing": 0,
            "average_pipeline_time": 0.0,
            "agent_performance": {}
        }
        
        logger.info("AgentOrchestrator initialized with 5-stage pipeline")
    
    async def process_document(self, document_data: Dict[str, Any], 
                              status_callback: Optional[callable] = None) -> Dict[str, Any]:
        """
        Process document through the complete agentic pipeline
        
        Args:
            document_data: Initial document data with content and metadata
            status_callback: Optional callback for status updates
            
        Returns:
            Complete processing results from all agents
        """
        start_time = asyncio.get_event_loop().time()
        document_id = document_data.get("document_id", "unknown")
        
        logger.info(f"Starting agentic pipeline for document {document_id}")
        
        # Initialize results dictionary
        pipeline_results = {
            "document_id": document_id,
            "pipeline_start_time": datetime.utcnow().isoformat(),
            "stages_completed": [],
            "current_stage": "initializing",
            "overall_success": False,
            "error_details": None,
            "agent_results": {}
        }
        
        try:
            # Pass data through each stage of the pipeline
            current_data = document_data.copy()
            
            for stage_name, agent in self.pipeline_stages:
                stage_start_time = asyncio.get_event_loop().time()
                
                try:
                    logger.info(f"Processing stage '{stage_name}' for document {document_id}")
                    
                    # Update status callback if provided
                    if status_callback:
                        await status_callback(document_id, stage_name, "processing")
                    
                    # Update pipeline status
                    pipeline_results["current_stage"] = stage_name
                    
                    # Process with current agent
                    agent_result = await agent.process(current_data)
                    
                    # Check if agent processing was successful
                    if not agent_result.get("success", False):
                        error_msg = f"Agent {agent.name} failed: {agent_result.get('error', 'Unknown error')}"
                        logger.error(error_msg)
                        pipeline_results["error_details"] = error_msg
                        
                        if status_callback:
                            await status_callback(document_id, stage_name, "failed")
                        
                        break
                    
                    # Store agent result
                    pipeline_results["agent_results"][stage_name] = agent_result
                    
                    # Update current data with results for next stage
                    current_data.update(agent_result)
                    
                    # Track stage completion
                    stage_time = asyncio.get_event_loop().time() - stage_start_time
                    pipeline_results["stages_completed"].append({
                        "stage": stage_name,
                        "agent": agent.name,
                        "completed_at": datetime.utcnow().isoformat(),
                        "processing_time": stage_time
                    })
                    
                    logger.info(f"Stage '{stage_name}' completed successfully for document {document_id}")
                    
                    if status_callback:
                        await status_callback(document_id, stage_name, "completed")
                
                except Exception as stage_error:
                    error_msg = f"Stage '{stage_name}' failed with error: {str(stage_error)}"
                    logger.error(error_msg)
                    pipeline_results["error_details"] = error_msg
                    
                    if status_callback:
                        await status_callback(document_id, stage_name, "error")
                    
                    break
            
            # Determine overall success
            pipeline_results["overall_success"] = len(pipeline_results["stages_completed"]) == len(self.pipeline_stages)
            pipeline_results["total_processing_time"] = asyncio.get_event_loop().time() - start_time
            pipeline_results["pipeline_end_time"] = datetime.utcnow().isoformat()
            
            # Update metrics
            await self._update_metrics(pipeline_results)
            
            if pipeline_results["overall_success"]:
                logger.info(f"Pipeline completed successfully for document {document_id}")
                if status_callback:
                    await status_callback(document_id, "completed", "success")
            else:
                logger.error(f"Pipeline failed for document {document_id}")
                if status_callback:
                    await status_callback(document_id, "failed", "error")
            
            return pipeline_results
            
        except Exception as e:
            total_time = asyncio.get_event_loop().time() - start_time
            error_msg = f"Pipeline orchestration failed: {str(e)}"
            logger.error(error_msg)
            
            pipeline_results.update({
                "overall_success": False,
                "error_details": error_msg,
                "total_processing_time": total_time,
                "pipeline_end_time": datetime.utcnow().isoformat()
            })
            
            if status_callback:
                await status_callback(document_id, "orchestration", "critical_error")
            
            return pipeline_results
    
    async def _update_metrics(self, pipeline_results: Dict[str, Any]):
        """Update orchestrator performance metrics"""
        self.metrics["documents_processed"] += 1
        
        if pipeline_results["overall_success"]:
            self.metrics["successful_completions"] += 1
        else:
            self.metrics["failed_processing"] += 1
        
        # Update average pipeline time
        total_time = pipeline_results.get("total_processing_time", 0.0)
        current_avg = self.metrics["average_pipeline_time"]
        processed_count = self.metrics["documents_processed"]
        
        self.metrics["average_pipeline_time"] = (
            (current_avg * (processed_count - 1) + total_time) / processed_count
        )
        
        # Update agent performance metrics
        for stage_info in pipeline_results.get("stages_completed", []):
            agent_name = stage_info.get("agent", "unknown")
            processing_time = stage_info.get("processing_time", 0.0)
            
            if agent_name not in self.metrics["agent_performance"]:
                self.metrics["agent_performance"][agent_name] = {
                    "total_calls": 0,
                    "successful_calls": 0,
                    "average_time": 0.0
                }
            
            agent_metrics = self.metrics["agent_performance"][agent_name]
            agent_metrics["total_calls"] += 1
            agent_metrics["successful_calls"] += 1
            
            # Update average time
            total_calls = agent_metrics["total_calls"]
            current_avg = agent_metrics["average_time"]
            agent_metrics["average_time"] = (
                (current_avg * (total_calls - 1) + processing_time) / total_calls
            )
    
    async def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status and metrics"""
        agent_statuses = {}
        
        for stage_name, agent in self.pipeline_stages:
            agent_statuses[stage_name] = {
                "agent_name": agent.name,
                "agent_version": agent.version,
                "status": agent.status,
                "metrics": agent.metrics
            }
        
        return {
            "orchestrator_metrics": self.metrics,
            "agent_statuses": agent_statuses,
            "pipeline_stages": [stage for stage, _ in self.pipeline_stages],
            "health_status": await self._check_pipeline_health()
        }
    
    async def _check_pipeline_health(self) -> Dict[str, Any]:
        """Check health of all agents in pipeline"""
        health_status = {
            "overall_healthy": True,
            "agent_health": {},
            "issues": []
        }
        
        for stage_name, agent in self.pipeline_stages:
            agent_healthy = True
            agent_issues = []
            
            # Check agent-specific health
            if hasattr(agent, 'health_check'):
                try:
                    agent_health = await agent.health_check()
                    agent_healthy = agent_health.get("status") in ["healthy", "simulation"]
                    if not agent_healthy:
                        agent_issues.append(agent_health.get("error", "Unknown health issue"))
                except Exception as e:
                    agent_healthy = False
                    agent_issues.append(f"Health check failed: {str(e)}")
            
            # Check basic agent status
            if agent.status not in ["active", "simulation"]:
                agent_healthy = False
                agent_issues.append(f"Agent status is {agent.status}")
            
            health_status["agent_health"][stage_name] = {
                "healthy": agent_healthy,
                "issues": agent_issues
            }
            
            if not agent_healthy:
                health_status["overall_healthy"] = False
                health_status["issues"].extend([f"{stage_name}: {issue}" for issue in agent_issues])
        
        return health_status
    
    async def process_batch(self, documents: List[Dict[str, Any]], 
                           max_concurrent: int = 3) -> List[Dict[str, Any]]:
        """
        Process multiple documents concurrently
        
        Args:
            documents: List of document data dictionaries
            max_concurrent: Maximum concurrent processing limit
            
        Returns:
            List of processing results
        """
        logger.info(f"Starting batch processing of {len(documents)} documents")
        
        # Create semaphore to limit concurrent processing
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_single(doc_data):
            async with semaphore:
                return await self.process_document(doc_data)
        
        # Process all documents concurrently with limit
        tasks = [process_single(doc) for doc in documents]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions in results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "document_id": documents[i].get("document_id", f"doc_{i}"),
                    "overall_success": False,
                    "error_details": f"Batch processing exception: {str(result)}"
                })
            else:
                processed_results.append(result)
        
        logger.info(f"Batch processing completed: {len(processed_results)} results")
        return processed_results
    
    async def get_agent_by_name(self, agent_name: str):
        """Get specific agent by name"""
        agent_map = {
            "validation_agent": self.validation_agent,
            "classification_agent": self.classification_agent,
            "mistral_ocr_agent": self.mistral_ocr_agent,
            "content_analysis_agent": self.content_analysis_agent,
            "schema_generation_agent": self.schema_generation_agent
        }
        return agent_map.get(agent_name)
    
    async def reset_metrics(self):
        """Reset all orchestrator metrics"""
        self.metrics = {
            "documents_processed": 0,
            "successful_completions": 0,
            "failed_processing": 0,
            "average_pipeline_time": 0.0,
            "agent_performance": {}
        }
        
        # Reset individual agent metrics
        for _, agent in self.pipeline_stages:
            agent.metrics = {
                "processed_count": 0,
                "success_count": 0,
                "error_count": 0,
                "average_processing_time": 0.0
            }
        
        logger.info("All metrics reset successfully")