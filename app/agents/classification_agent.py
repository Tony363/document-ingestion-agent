"""
Classification Agent - Document type and complexity detection
Determines document type and processing complexity before OCR
"""

import asyncio
import logging
import re
from typing import Dict, Any, List, Tuple
from datetime import datetime
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class ClassificationAgent(BaseAgent):
    """Agent responsible for document classification and complexity analysis"""
    
    def __init__(self):
        super().__init__("classification_agent", "1.0.0")
        
        # Document type patterns for classification
        self.document_patterns = {
            "invoice": {
                "keywords": ["invoice", "inv #", "invoice number", "bill to", "total amount", "due date"],
                "patterns": [
                    r"invoice\s*#?\s*:?\s*\d+",
                    r"inv\s*#?\s*:?\s*\d+", 
                    r"bill\s*to",
                    r"total\s*amount",
                    r"due\s*date"
                ]
            },
            "receipt": {
                "keywords": ["receipt", "thank you", "cash", "card", "payment", "purchase"],
                "patterns": [
                    r"receipt\s*#?\s*:?\s*\d+",
                    r"thank\s*you\s*for\s*your",
                    r"cash|card|credit",
                    r"purchase\s*date"
                ]
            },
            "contract": {
                "keywords": ["contract", "agreement", "party", "terms", "conditions", "signature"],
                "patterns": [
                    r"this\s*agreement",
                    r"contract\s*between",
                    r"terms\s*and\s*conditions",
                    r"signature\s*date"
                ]
            },
            "form": {
                "keywords": ["form", "application", "name:", "date:", "please fill", "check one"],
                "patterns": [
                    r"application\s*form",
                    r"please\s*(fill|complete)",
                    r"check\s*one",
                    r"name\s*:?\s*_+",
                    r"date\s*:?\s*_+"
                ]
            }
        }
        
        # Complexity indicators
        self.complexity_indicators = {
            "high": ["table", "graph", "chart", "diagram", "multi-column"],
            "medium": ["list", "bullet", "numbered", "form field"],
            "low": ["paragraph", "simple text", "header"]
        }
        
        self.status = "active"
        logger.info("ClassificationAgent initialized with document type patterns")
    
    async def process(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify document type and analyze complexity
        
        Args:
            document_data: Contains document metadata and content
            
        Returns:
            Classification results with document type and complexity
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            if not await self.validate_input(document_data):
                raise ValueError("Invalid input data for classification")
            
            document_id = document_data["document_id"]
            file_metadata = document_data.get("file_metadata", {})
            content = document_data.get("content", b"")
            
            logger.info(f"Classifying document {document_id}")
            
            # Step 1: Basic metadata analysis
            metadata_analysis = await self._analyze_metadata(file_metadata)
            
            # Step 2: Content-based classification (if we can extract sample text)
            content_analysis = await self._analyze_content_sample(content, file_metadata)
            
            # Step 3: Determine document type
            document_type, confidence = await self._determine_document_type(
                metadata_analysis, content_analysis
            )
            
            # Step 4: Assess processing complexity
            complexity_assessment = await self._assess_complexity(
                content, file_metadata, content_analysis
            )
            
            # Step 5: Generate processing recommendations
            processing_recommendations = await self._generate_processing_recommendations(
                document_type, complexity_assessment, file_metadata
            )
            
            processing_time = asyncio.get_event_loop().time() - start_time
            self.update_metrics(True, processing_time)
            
            result = {
                "success": True,
                "document_id": document_id,
                "classification": {
                    "document_type": document_type,
                    "confidence": confidence,
                    "alternative_types": content_analysis.get("alternative_types", [])
                },
                "complexity_assessment": complexity_assessment,
                "processing_recommendations": processing_recommendations,
                "metadata_analysis": metadata_analysis,
                "content_analysis": content_analysis,
                "processing_time": processing_time,
                "agent": self.name,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Classification completed for document {document_id}: {document_type} (confidence: {confidence})")
            return result
            
        except Exception as e:
            processing_time = asyncio.get_event_loop().time() - start_time
            self.update_metrics(False, processing_time)
            return await self.handle_error(e, document_data.get("document_id", "unknown"))
    
    async def _analyze_metadata(self, file_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze file metadata for classification hints"""
        analysis = {
            "filename_hints": [],
            "size_category": "",
            "format_indicators": []
        }
        
        filename = file_metadata.get("filename", "").lower()
        file_size = file_metadata.get("size", 0)
        mime_type = file_metadata.get("mime_type", "")
        
        # Analyze filename for hints
        filename_patterns = {
            "invoice": ["invoice", "inv", "bill"],
            "receipt": ["receipt", "rcpt", "purchase"],
            "contract": ["contract", "agreement", "terms"],
            "form": ["form", "application", "app"]
        }
        
        for doc_type, patterns in filename_patterns.items():
            for pattern in patterns:
                if pattern in filename:
                    analysis["filename_hints"].append(doc_type)
        
        # Categorize by size
        if file_size < 100 * 1024:  # < 100KB
            analysis["size_category"] = "small"
        elif file_size < 1024 * 1024:  # < 1MB
            analysis["size_category"] = "medium" 
        else:
            analysis["size_category"] = "large"
        
        # Format indicators
        if mime_type == "application/pdf":
            format_info = file_metadata.get("format_info", {}).get("properties", {})
            analysis["format_indicators"] = {
                "has_text_layer": format_info.get("has_text_layer", False),
                "estimated_pages": format_info.get("estimated_pages", 1),
                "pdf_version": format_info.get("pdf_version", "unknown")
            }
        
        return analysis
    
    async def _analyze_content_sample(self, content: bytes, file_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a sample of content for classification hints"""
        analysis = {
            "text_sample": "",
            "detected_patterns": {},
            "language_hints": [],
            "structure_indicators": [],
            "alternative_types": []
        }
        
        try:
            # For simulation, we'll work with sample content
            # In production, this would extract first page or text sample
            
            mime_type = file_metadata.get("mime_type", "")
            
            if mime_type == "application/pdf":
                # Check if PDF has text layer for quick analysis
                has_text_layer = file_metadata.get("format_info", {}).get("properties", {}).get("has_text_layer", False)
                
                if has_text_layer:
                    # Simulate text extraction from first page
                    sample_text = self._simulate_pdf_text_sample(content)
                    analysis["text_sample"] = sample_text
                    analysis["detected_patterns"] = await self._detect_patterns(sample_text)
                else:
                    # Will need OCR, can't analyze content beforehand
                    analysis["structure_indicators"] = ["requires_ocr"]
            
            elif mime_type.startswith("image/"):
                # Image documents require OCR
                analysis["structure_indicators"] = ["image_document", "requires_ocr"]
            
        except Exception as e:
            logger.warning(f"Content sample analysis failed: {str(e)}")
        
        return analysis
    
    def _simulate_pdf_text_sample(self, content: bytes) -> str:
        """Simulate extracting text sample from PDF for classification"""
        # In production, this would use PyPDF2 or similar to extract first page
        return """
        INVOICE
        Invoice Number: INV-12345
        Date: 2025-01-15
        Bill To: Sample Customer
        Total Amount: $145.80
        """
    
    async def _detect_patterns(self, text: str) -> Dict[str, List[str]]:
        """Detect document type patterns in text"""
        detected = {}
        text_lower = text.lower()
        
        for doc_type, config in self.document_patterns.items():
            matches = []
            
            # Check keyword matches
            for keyword in config["keywords"]:
                if keyword.lower() in text_lower:
                    matches.append(f"keyword: {keyword}")
            
            # Check regex patterns
            for pattern in config["patterns"]:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    matches.append(f"pattern: {pattern}")
            
            if matches:
                detected[doc_type] = matches
        
        return detected
    
    async def _determine_document_type(self, metadata_analysis: Dict[str, Any], content_analysis: Dict[str, Any]) -> Tuple[str, float]:
        """Determine document type with confidence score"""
        scores = {}
        
        # Score based on filename hints
        for hint in metadata_analysis.get("filename_hints", []):
            scores[hint] = scores.get(hint, 0) + 0.3
        
        # Score based on content patterns
        detected_patterns = content_analysis.get("detected_patterns", {})
        for doc_type, matches in detected_patterns.items():
            pattern_score = len(matches) * 0.2
            scores[doc_type] = scores.get(doc_type, 0) + pattern_score
        
        # Default classification if no clear match
        if not scores:
            return "unknown", 0.1
        
        # Find highest scoring type
        best_type = max(scores.keys(), key=lambda k: scores[k])
        confidence = min(scores[best_type], 1.0)  # Cap at 1.0
        
        # Require minimum confidence threshold
        if confidence < 0.3:
            return "unknown", confidence
        
        return best_type, confidence
    
    async def _assess_complexity(self, content: bytes, file_metadata: Dict[str, Any], content_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Assess document processing complexity"""
        complexity = {
            "level": "medium",  # low, medium, high
            "factors": [],
            "estimated_processing_time": 2.0,  # seconds
            "ocr_requirements": {
                "required": True,
                "complexity": "standard"
            }
        }
        
        # Size-based complexity
        file_size = file_metadata.get("size", 0)
        if file_size > 5 * 1024 * 1024:  # > 5MB
            complexity["factors"].append("large_file_size")
            complexity["level"] = "high"
            complexity["estimated_processing_time"] = 10.0
        
        # Page count complexity
        estimated_pages = file_metadata.get("format_info", {}).get("properties", {}).get("estimated_pages", 1)
        if estimated_pages > 10:
            complexity["factors"].append("multi_page_document")
            complexity["level"] = "high"
        
        # Check if OCR can be bypassed
        mime_type = file_metadata.get("mime_type", "")
        if mime_type == "application/pdf":
            has_text_layer = file_metadata.get("format_info", {}).get("properties", {}).get("has_text_layer", False)
            if has_text_layer:
                complexity["ocr_requirements"]["required"] = False
                complexity["factors"].append("native_text_available")
                complexity["level"] = "low"
                complexity["estimated_processing_time"] = 0.5
        
        return complexity
    
    async def _generate_processing_recommendations(self, document_type: str, complexity: Dict[str, Any], file_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Generate processing recommendations based on classification"""
        recommendations = {
            "processing_route": "standard",
            "optimizations": [],
            "cost_estimate": 0.001,  # Base cost per page
            "suggested_agents": ["mistral_ocr_agent", "content_analysis_agent", "schema_generation_agent"]
        }
        
        # Route optimization based on complexity
        if not complexity["ocr_requirements"]["required"]:
            recommendations["processing_route"] = "native_text_extraction"
            recommendations["optimizations"].append("bypass_ocr")
            recommendations["cost_estimate"] = 0.0  # No OCR cost
        
        # Document type specific optimizations
        if document_type == "invoice":
            recommendations["suggested_agents"].extend(["table_extraction_agent"])
            recommendations["optimizations"].append("structured_extraction")
        
        elif document_type == "form":
            recommendations["suggested_agents"].extend(["field_detection_agent"])
            recommendations["optimizations"].append("form_field_detection")
        
        return recommendations