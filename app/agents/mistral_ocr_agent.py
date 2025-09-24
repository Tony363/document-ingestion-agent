"""
Mistral OCR Agent

Interfaces with Mistral AI's OCR API for text extraction from documents.
Handles PDF and image processing with retry logic and rate limiting.
"""

import asyncio
import base64
from typing import Optional, Dict, Any, List
from pathlib import Path
import httpx
from pydantic import BaseModel, Field
import PyPDF2
from PIL import Image
import io
import logging

from .base_agent import BaseAgent, AgentContext

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
    Agent for OCR processing using Mistral AI API
    """
    
    def __init__(
        self,
        api_key: str,
        api_url: str = "https://api.mistral.ai/v1/ocr",
        max_file_size_mb: int = 10,
        rate_limit_delay: float = 0.1
    ):
        super().__init__(
            name="mistral_ocr_agent",
            max_retries=3,
            timeout=60.0
        )
        self.api_key = api_key
        self.api_url = api_url
        self.max_file_size_mb = max_file_size_mb
        self.rate_limit_delay = rate_limit_delay
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=httpx.Timeout(60.0)
        )
        
    async def validate_input(self, input_data: OCRInput) -> bool:
        """Validate OCR input"""
        if not input_data.file_path:
            return False
            
        path = Path(input_data.file_path)
        if not path.exists():
            self.logger.error(f"File not found: {input_data.file_path}")
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
        
        file_path = Path(input_data.file_path)
        
        # Check if PDF has extractable text first
        if input_data.mime_type == "application/pdf":
            extracted_text = await self._extract_pdf_text(file_path)
            if extracted_text and len(extracted_text.strip()) > 100:
                # PDF has digital text, skip OCR
                self.logger.info("PDF has extractable text, skipping OCR")
                pages = [
                    OCRPage(
                        page_number=1,
                        text=extracted_text,
                        confidence=1.0,
                        word_count=len(extracted_text.split())
                    )
                ]
                
                processing_time = int((time.time() - start_time) * 1000)
                
                return OCROutput(
                    total_pages=1,
                    processed_pages=1,
                    full_text=extracted_text,
                    pages=pages,
                    average_confidence=1.0,
                    processing_time_ms=processing_time,
                    metadata={"method": "pdf_extraction"}
                )
        
        # Process with OCR
        pages = []
        
        if input_data.mime_type == "application/pdf":
            # Process PDF pages
            pages = await self._process_pdf_ocr(file_path, input_data.page_numbers)
        else:
            # Process image
            pages = await self._process_image_ocr(file_path)
        
        # Combine results
        full_text = "\n\n".join([page.text for page in pages])
        average_confidence = (
            sum(page.confidence for page in pages) / len(pages)
            if pages else 0.0
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return OCROutput(
            total_pages=len(pages),
            processed_pages=len(pages),
            full_text=full_text,
            pages=pages,
            average_confidence=average_confidence,
            processing_time_ms=processing_time,
            metadata={
                "method": "mistral_ocr",
                "document_type": input_data.document_type
            }
        )
    
    async def _extract_pdf_text(self, file_path: Path) -> Optional[str]:
        """
        Extract text from PDF if it's digital (not scanned)
        
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
            self.logger.warning(f"Failed to extract PDF text: {e}")
            return None
    
    async def _process_pdf_ocr(
        self,
        file_path: Path,
        page_numbers: Optional[List[int]] = None
    ) -> List[OCRPage]:
        """
        Process PDF with Mistral OCR
        
        Args:
            file_path: Path to PDF file
            page_numbers: Specific pages to process
            
        Returns:
            List of OCR results per page
        """
        pages = []
        
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                total_pages = len(reader.pages)
                
                # Determine pages to process
                if page_numbers:
                    pages_to_process = [p for p in page_numbers if 0 < p <= total_pages]
                else:
                    pages_to_process = range(1, min(total_pages + 1, 10))  # Limit to 10 pages
                
                for page_num in pages_to_process:
                    # Convert PDF page to image
                    # In production, use pdf2image or similar
                    # For now, we'll send the PDF directly to Mistral
                    
                    # Rate limiting
                    await asyncio.sleep(self.rate_limit_delay)
                    
                    # Process page with Mistral OCR
                    page_result = await self._call_mistral_ocr(
                        file_path,
                        page_number=page_num
                    )
                    
                    if page_result:
                        pages.append(page_result)
                        
        except Exception as e:
            self.logger.error(f"PDF OCR processing failed: {e}")
            
        return pages
    
    async def _process_image_ocr(self, file_path: Path) -> List[OCRPage]:
        """
        Process image with Mistral OCR
        
        Args:
            file_path: Path to image file
            
        Returns:
            List with single OCR result
        """
        page_result = await self._call_mistral_ocr(file_path)
        return [page_result] if page_result else []
    
    async def _call_mistral_ocr(
        self,
        file_path: Path,
        page_number: int = 1
    ) -> Optional[OCRPage]:
        """
        Call Mistral OCR API
        
        Args:
            file_path: Path to file
            page_number: Page number being processed
            
        Returns:
            OCR result for the page
        """
        try:
            # Read and encode file
            with open(file_path, 'rb') as file:
                file_content = file.read()
                file_base64 = base64.b64encode(file_content).decode('utf-8')
            
            # Prepare request payload
            payload = {
                "file": file_base64,
                "file_type": file_path.suffix[1:],  # Remove the dot
                "ocr_options": {
                    "language": "en",
                    "detect_tables": True,
                    "detect_layout": True
                }
            }
            
            # Add page specification for PDFs
            if file_path.suffix.lower() == '.pdf':
                payload["page_number"] = page_number
            
            # Call Mistral OCR API
            response = await self.client.post(
                self.api_url,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract text and metadata
                extracted_text = result.get("text", "")
                confidence = result.get("confidence", 0.0)
                has_tables = result.get("has_tables", False)
                has_images = result.get("has_images", False)
                
                return OCRPage(
                    page_number=page_number,
                    text=extracted_text,
                    confidence=confidence,
                    word_count=len(extracted_text.split()),
                    has_tables=has_tables,
                    has_images=has_images
                )
            
            elif response.status_code == 429:
                # Rate limited
                self.logger.warning("Rate limited by Mistral API")
                await asyncio.sleep(self.rate_limit_delay * 10)
                return None
                
            else:
                self.logger.error(f"Mistral OCR API error: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to call Mistral OCR: {e}")
            return None
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - close HTTP client"""
        await self.client.aclose()