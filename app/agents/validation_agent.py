"""
Validation Agent - First agent in the pipeline
Handles file format validation, security scanning, and size limits
"""

import magic
import hashlib
from typing import Dict, Any
from pathlib import Path
import asyncio
import logging
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class ValidationAgent(BaseAgent):
    """Agent responsible for validating uploaded documents"""
    
    def __init__(self):
        super().__init__("validation_agent", "1.0.0")
        
        # Supported MIME types for PDF and images
        self.supported_mime_types = {
            "application/pdf",
            "image/jpeg",
            "image/jpg", 
            "image/png",
            "image/tiff",
            "image/bmp"
        }
        
        # File size limits
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.min_file_size = 100  # 100 bytes
        
        # Security patterns to detect potentially malicious content
        self.suspicious_patterns = [
            b"<script",
            b"javascript:",
            b"eval(",
            b"exec(",
            b"system(",
            b"shell_exec("
        ]
        
        self.status = "active"
        logger.info(f"ValidationAgent initialized with support for: {self.supported_mime_types}")
    
    async def process(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate document format, size, and security
        
        Args:
            document_data: Contains document_id, filename, content, content_type
            
        Returns:
            Validation results with file metadata
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Validate input
            if not await self.validate_input(document_data):
                raise ValueError("Invalid input data for validation")
            
            document_id = document_data["document_id"]
            filename = document_data.get("filename", "unknown")
            content = document_data["content"]
            declared_content_type = document_data.get("content_type")
            
            logger.info(f"Validating document {document_id}: {filename}")
            
            # Step 1: Size validation
            file_size = len(content)
            if file_size > self.max_file_size:
                raise ValueError(f"File too large: {file_size} bytes (max: {self.max_file_size})")
            
            if file_size < self.min_file_size:
                raise ValueError(f"File too small: {file_size} bytes (min: {self.min_file_size})")
            
            # Step 2: MIME type detection using python-magic
            detected_mime_type = magic.from_buffer(content, mime=True)
            
            if detected_mime_type not in self.supported_mime_types:
                raise ValueError(f"Unsupported file type: {detected_mime_type}")
            
            # Step 3: File extension validation
            file_extension = Path(filename).suffix.lower()
            expected_extensions = self._get_expected_extensions(detected_mime_type)
            
            if file_extension not in expected_extensions:
                logger.warning(
                    f"File extension mismatch: {file_extension} for MIME type {detected_mime_type}"
                )
            
            # Step 4: Security scanning
            security_scan_result = await self._security_scan(content, document_id)
            if not security_scan_result["safe"]:
                raise ValueError(f"Security scan failed: {security_scan_result['reason']}")
            
            # Step 5: Generate file hash for integrity
            file_hash = hashlib.sha256(content).hexdigest()
            
            # Step 6: Determine document format specifics
            format_info = await self._analyze_format_specifics(content, detected_mime_type)
            
            processing_time = asyncio.get_event_loop().time() - start_time
            self.update_metrics(True, processing_time)
            
            result = {
                "success": True,
                "document_id": document_id,
                "validation_status": "passed",
                "file_metadata": {
                    "filename": filename,
                    "size": file_size,
                    "mime_type": detected_mime_type,
                    "declared_content_type": declared_content_type,
                    "file_extension": file_extension,
                    "file_hash": file_hash,
                    "format_info": format_info
                },
                "security_scan": security_scan_result,
                "processing_time": processing_time,
                "agent": self.name,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            logger.info(f"Validation successful for document {document_id}")
            return result
            
        except Exception as e:
            processing_time = asyncio.get_event_loop().time() - start_time
            self.update_metrics(False, processing_time)
            return await self.handle_error(e, document_data.get("document_id", "unknown"))
    
    def _get_expected_extensions(self, mime_type: str) -> set:
        """Get expected file extensions for MIME type"""
        mime_to_extensions = {
            "application/pdf": {".pdf"},
            "image/jpeg": {".jpg", ".jpeg"},
            "image/png": {".png"},
            "image/tiff": {".tiff", ".tif"},
            "image/bmp": {".bmp"}
        }
        return mime_to_extensions.get(mime_type, set())
    
    async def _security_scan(self, content: bytes, document_id: str) -> Dict[str, Any]:
        """
        Perform basic security scanning on file content
        """
        scan_result = {
            "safe": True,
            "reason": None,
            "threats_detected": []
        }
        
        try:
            # Check for suspicious patterns
            content_lower = content.lower()
            
            for pattern in self.suspicious_patterns:
                if pattern in content_lower:
                    scan_result["threats_detected"].append(pattern.decode('utf-8', errors='ignore'))
            
            # Basic entropy check for potentially encrypted/malicious content
            entropy = self._calculate_entropy(content[:1024])  # Check first 1KB
            if entropy > 7.5:  # High entropy might indicate encryption/compression
                logger.warning(f"High entropy detected in document {document_id}: {entropy}")
            
            # If threats detected, mark as unsafe
            if scan_result["threats_detected"]:
                scan_result["safe"] = False
                scan_result["reason"] = f"Suspicious patterns detected: {scan_result['threats_detected']}"
            
            return scan_result
            
        except Exception as e:
            logger.error(f"Security scan error for document {document_id}: {str(e)}")
            return {
                "safe": False,
                "reason": f"Security scan failed: {str(e)}",
                "threats_detected": []
            }
    
    def _calculate_entropy(self, data: bytes) -> float:
        """Calculate Shannon entropy of data"""
        if len(data) == 0:
            return 0
        
        frequency = {}
        for byte in data:
            frequency[byte] = frequency.get(byte, 0) + 1
        
        entropy = 0
        length = len(data)
        
        for count in frequency.values():
            probability = count / length
            if probability > 0:
                entropy -= probability * (probability.bit_length() - 1)
        
        return entropy
    
    async def _analyze_format_specifics(self, content: bytes, mime_type: str) -> Dict[str, Any]:
        """
        Analyze format-specific properties
        """
        format_info = {
            "type": mime_type,
            "properties": {}
        }
        
        try:
            if mime_type == "application/pdf":
                # Basic PDF analysis
                format_info["properties"] = {
                    "has_text_layer": b"stream" in content[:2048],  # Rough heuristic
                    "estimated_pages": content.count(b"/Page"),
                    "pdf_version": self._extract_pdf_version(content)
                }
            
            elif mime_type.startswith("image/"):
                # Basic image analysis
                format_info["properties"] = {
                    "format": mime_type.split("/")[1],
                    "size_bytes": len(content)
                }
            
            return format_info
            
        except Exception as e:
            logger.warning(f"Format analysis error: {str(e)}")
            return format_info
    
    def _extract_pdf_version(self, content: bytes) -> str:
        """Extract PDF version from header"""
        try:
            header = content[:20].decode('ascii', errors='ignore')
            if header.startswith('%PDF-'):
                return header[5:8]
        except:
            pass
        return "unknown"