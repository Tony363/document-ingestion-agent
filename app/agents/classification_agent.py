"""
Document Classification Agent

Classifies documents based on their content and structure.
Supports: invoices, receipts, contracts, forms, and generic documents.
"""

from typing import Optional, Dict, Any
import magic
import mimetypes
from pathlib import Path
from pydantic import BaseModel, Field

from .base_agent import BaseAgent, AgentContext
from ..config import settings

class ClassificationInput(BaseModel):
    """Input for document classification"""
    file_path: str
    mime_type: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None

class ClassificationOutput(BaseModel):
    """Output from document classification"""
    document_type: str
    confidence: float
    mime_type: str
    file_extension: str
    is_supported: bool
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ClassificationAgent(BaseAgent[ClassificationInput, ClassificationOutput]):
    """
    Agent for classifying document types based on file metadata and initial content
    """
    
    SUPPORTED_MIME_TYPES = {
        "application/pdf",
        "image/png",
        "image/jpeg",
        "image/jpg",
        "image/tiff",
        "image/bmp"
    }
    
    DOCUMENT_TYPE_PATTERNS = {
        "invoice": ["invoice", "bill", "statement", "total", "amount due"],
        "receipt": ["receipt", "payment", "transaction", "purchased"],
        "contract": ["agreement", "contract", "terms", "parties", "whereas"],
        "nda": ["non-disclosure", "nondisclosure", "nda", "confidentiality agreement", "proprietary information", "disclosing party", "receiving party"],
        "form": ["form", "application", "questionnaire", "checkbox"]
    }
    
    def __init__(self):
        super().__init__(
            name="classification_agent",
            max_retries=2,
            timeout=10.0
        )
        
    async def validate_input(self, input_data: ClassificationInput) -> bool:
        """Validate classification input"""
        if not input_data.file_path:
            return False
            
        # Resolve full path using environment-aware method
        full_path = Path(settings.get_upload_path()) / input_data.file_path
        if not full_path.exists():
            self.logger.error(f"File not found: {full_path}")
            return False
            
        return True
    
    async def process(
        self,
        input_data: ClassificationInput,
        context: AgentContext
    ) -> ClassificationOutput:
        """
        Classify document type based on file metadata
        
        Args:
            input_data: Classification input with file path
            context: Agent execution context
            
        Returns:
            Classification output with document type and confidence
        """
        # Resolve full path using environment-aware method
        file_path = Path(settings.get_upload_path()) / input_data.file_path
        
        # Detect MIME type if not provided
        if input_data.mime_type:
            mime_type = input_data.mime_type
        else:
            # Try multiple methods to detect MIME type
            mime_type = await self._detect_mime_type(file_path)
        
        # Get file extension
        file_extension = file_path.suffix.lower()
        
        # Check if supported
        is_supported = mime_type in self.SUPPORTED_MIME_TYPES
        
        # Classify document type
        document_type = await self._classify_document_type(
            file_path,
            mime_type,
            file_extension
        )
        
        # Calculate confidence based on classification method
        confidence = await self._calculate_confidence(
            document_type,
            mime_type,
            is_supported
        )
        
        # Gather metadata
        metadata = {
            "file_name": file_path.name,
            "file_size": file_path.stat().st_size,
            "file_extension": file_extension,
            "detected_mime": mime_type
        }
        
        return ClassificationOutput(
            document_type=document_type,
            confidence=confidence,
            mime_type=mime_type,
            file_extension=file_extension,
            is_supported=is_supported,
            metadata=metadata
        )
    
    async def _detect_mime_type(self, file_path: Path) -> str:
        """
        Detect MIME type using multiple methods
        
        Args:
            file_path: Path to file
            
        Returns:
            Detected MIME type
        """
        try:
            # Try python-magic first (most reliable)
            mime = magic.Magic(mime=True)
            mime_type = mime.from_file(str(file_path))
            
            if mime_type:
                return mime_type
        except Exception as e:
            self.logger.warning(f"python-magic failed: {e}")
        
        # Fallback to mimetypes
        mime_type, _ = mimetypes.guess_type(str(file_path))
        
        if mime_type:
            return mime_type
            
        # Default based on extension
        extension_map = {
            ".pdf": "application/pdf",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".tiff": "image/tiff",
            ".tif": "image/tiff",
            ".bmp": "image/bmp"
        }
        
        return extension_map.get(file_path.suffix.lower(), "application/octet-stream")
    
    async def _classify_document_type(
        self,
        file_path: Path,
        mime_type: str,
        file_extension: str
    ) -> str:
        """
        Classify document type based on available information
        
        Args:
            file_path: Path to document
            mime_type: MIME type of document
            file_extension: File extension
            
        Returns:
            Document type classification
        """
        # Check file name patterns
        file_name_lower = file_path.name.lower()
        
        # First check for NDA specifically
        if "nda" in file_name_lower or "non-disclosure" in file_name_lower or "nondisclosure" in file_name_lower:
            return "nda"
        
        for doc_type, patterns in self.DOCUMENT_TYPE_PATTERNS.items():
            for pattern in patterns:
                if pattern in file_name_lower:
                    return doc_type
        
        # Default classification based on common patterns
        if "inv" in file_name_lower:
            return "invoice"
        elif "rec" in file_name_lower or "rcpt" in file_name_lower:
            return "receipt"
        elif "contract" in file_name_lower or "agreement" in file_name_lower:
            return "contract"
        elif "form" in file_name_lower:
            return "form"
        
        # Default to generic document
        return "document"
    
    async def _calculate_confidence(
        self,
        document_type: str,
        mime_type: str,
        is_supported: bool
    ) -> float:
        """
        Calculate classification confidence score
        
        Args:
            document_type: Classified document type
            mime_type: MIME type
            is_supported: Whether format is supported
            
        Returns:
            Confidence score between 0 and 1
        """
        confidence = 0.5  # Base confidence
        
        # Boost for supported formats
        if is_supported:
            confidence += 0.2
        
        # Boost for specific document types vs generic
        if document_type != "document":
            confidence += 0.2
        
        # Boost for PDF (most reliable for text extraction)
        if mime_type == "application/pdf":
            confidence += 0.1
        
        return min(confidence, 1.0)