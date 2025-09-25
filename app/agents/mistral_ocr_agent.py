"""
Mistral OCR Agent

Uses Mistral AI's OCR API for text extraction from documents.
Handles PDF and image processing with the mistral-ocr-latest model.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
from pydantic import BaseModel, Field
import PyPDF2
import json

from mistralai import Mistral

from .base_agent import BaseAgent, AgentContext
from ..config import settings

class OCRInput(BaseModel):
    """Input for OCR processing"""
    file_path: str
    mime_type: str
    document_type: Optional[str] = "unknown"
    page_numbers: Optional[List[int]] = None  # Specific pages to process
    
class OCRPage(BaseModel):
    """OCR result for a single page"""
    page_number: int
    text: str
    confidence: float
    word_count: int
    has_tables: bool = False
    has_images: bool = False

class OCROutput(BaseModel):
    """Output from OCR processing"""
    total_pages: int
    processed_pages: int
    full_text: str
    pages: List[OCRPage]
    average_confidence: float
    processing_time_ms: int
    metadata: Dict[str, Any] = Field(default_factory=dict)

class MistralOCRAgent(BaseAgent[OCRInput, OCROutput]):
    """
    Agent for OCR processing using Mistral AI's OCR API
    """
    
    def __init__(
        self,
        api_key: str,
        max_file_size_mb: int = 10,
        rate_limit_delay: float = 0.1
    ):
        super().__init__(
            name="mistral_ocr_agent",
            max_retries=3,
            timeout=60.0
        )
        self.api_key = api_key
        self.max_file_size_mb = max_file_size_mb
        self.rate_limit_delay = rate_limit_delay
        
        # Initialize Mistral client with SDK
        self.client = Mistral(api_key=api_key)
        
    async def validate_input(self, input_data: OCRInput) -> bool:
        """Validate OCR input"""
        if not input_data.file_path:
            return False
            
        # Resolve full path using environment-aware method
        path = Path(settings.get_upload_path()) / input_data.file_path
        if not path.exists():
            self.logger.error(f"File not found: {path}")
            return False
            
        # Check file size
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.max_file_size_mb:
            self.logger.error(f"File too large: {file_size_mb}MB > {self.max_file_size_mb}MB")
            return False
            
        return True
    
    async def process(
        self,
        input_data: OCRInput,
        context: AgentContext
    ) -> OCROutput:
        """
        Process document with Mistral OCR API
        
        Args:
            input_data: OCR input with file path and metadata
            context: Agent execution context
            
        Returns:
            OCR output with extracted text and metadata
        """
        import time
        start_time = time.time()
        
        # Resolve full path using environment-aware method
        file_path = Path(settings.get_upload_path()) / input_data.file_path
        
        # Process with Mistral OCR API
        pages = []
        
        try:
            # Call Mistral OCR API
            self.logger.info(f"Processing document with Mistral OCR: {file_path}")
            
            # Use Mistral OCR API with base64 encoding
            import base64
            with open(file_path, 'rb') as file:
                try:
                    # Convert file to base64 for Mistral API
                    file_content = file.read()
                    base64_content = base64.b64encode(file_content).decode('utf-8')
                    
                    # Determine MIME type for data URL
                    mime_type = input_data.mime_type or "application/pdf"
                    data_url = f"data:{mime_type};base64,{base64_content}"
                    
                    # Process the document using Mistral OCR
                    ocr_response = await asyncio.to_thread(
                        self.client.ocr.process,
                        model="mistral-ocr-latest",
                        document={
                            "type": "document_url",
                            "document_url": data_url
                        },
                        include_image_base64=False  # We don't need base64 images back
                    )
                    
                    # Extract text and metadata from response
                    if hasattr(ocr_response, 'text'):
                        extracted_text = ocr_response.text
                    elif hasattr(ocr_response, 'content'):
                        extracted_text = ocr_response.content
                    elif isinstance(ocr_response, dict):
                        extracted_text = ocr_response.get('text', '') or ocr_response.get('content', '')
                    else:
                        # Try to extract text from string representation
                        extracted_text = str(ocr_response)
                    
                    # Get confidence score if available
                    confidence = 0.95  # Default high confidence for OCR API
                    if hasattr(ocr_response, 'confidence'):
                        confidence = ocr_response.confidence
                    elif isinstance(ocr_response, dict) and 'confidence' in ocr_response:
                        confidence = ocr_response['confidence']
                    
                    # Check for tables
                    has_tables = False
                    if hasattr(ocr_response, 'tables'):
                        has_tables = len(ocr_response.tables) > 0
                    elif isinstance(ocr_response, dict) and 'tables' in ocr_response:
                        has_tables = len(ocr_response.get('tables', [])) > 0
                    
                    # Create page result
                    if extracted_text:
                        pages.append(OCRPage(
                            page_number=1,
                            text=extracted_text,
                            confidence=confidence,
                            word_count=len(extracted_text.split()),
                            has_tables=has_tables,
                            has_images=input_data.mime_type.startswith("image/")
                        ))
                        
                        self.logger.info(f"Successfully extracted {len(extracted_text)} characters with confidence {confidence}")
                    else:
                        self.logger.warning("No text extracted from OCR response")
                        
                except Exception as e:
                    self.logger.error(f"Error calling Mistral OCR API: {e}")
                    
                    # Fallback to basic PDF text extraction if available
                    if input_data.mime_type == "application/pdf":
                        try:
                            extracted_text = await self._extract_pdf_text_fallback(file_path)
                            if extracted_text:
                                pages.append(OCRPage(
                                    page_number=1,
                                    text=extracted_text,
                                    confidence=0.7,  # Lower confidence for fallback
                                    word_count=len(extracted_text.split()),
                                    has_tables=False,
                                    has_images=False
                                ))
                                self.logger.info(f"Fallback: Extracted {len(extracted_text)} characters from PDF")
                        except Exception as fallback_error:
                            self.logger.error(f"Fallback extraction also failed: {fallback_error}")
                    
        except Exception as e:
            self.logger.error(f"Failed to process document: {e}")
        
        # Combine results
        if pages:
            full_text = "\n\n".join([page.text for page in pages])
            average_confidence = sum(page.confidence for page in pages) / len(pages)
        else:
            # Return empty result if no extraction succeeded
            full_text = ""
            average_confidence = 0.0
            pages = [OCRPage(
                page_number=1,
                text="",
                confidence=0.0,
                word_count=0,
                has_tables=False,
                has_images=False
            )]
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return OCROutput(
            total_pages=len(pages),
            processed_pages=len(pages),
            full_text=full_text,
            pages=pages,
            average_confidence=average_confidence,
            processing_time_ms=processing_time,
            metadata={
                "method": "mistral_ocr_api",
                "document_type": input_data.document_type,
                "model": "mistral-ocr-latest"
            }
        )
    
    async def _extract_pdf_text_fallback(self, file_path: Path) -> Optional[str]:
        """
        Fallback: Extract text from PDF if OCR fails
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text or None if not extractable
        """
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                
                return text if text.strip() else None
                
        except Exception as e:
            self.logger.warning(f"Failed to extract PDF text in fallback: {e}")
            return None