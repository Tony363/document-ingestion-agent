"""
Content Analysis Agent - Intelligent content understanding
Analyzes extracted content to determine structure and extract key information
"""

import asyncio
import logging
import re
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class ContentAnalysisAgent(BaseAgent):
    """Agent responsible for analyzing and structuring extracted content"""
    
    def __init__(self):
        super().__init__("content_analysis_agent", "1.0.0")
        
        # Field extraction patterns by document type
        self.extraction_patterns = {
            "invoice": {
                "invoice_number": [
                    r"invoice\s*#?:?\s*([A-Z0-9-]+)",
                    r"inv\s*#?:?\s*([A-Z0-9-]+)",
                    r"invoice\s*number:?\s*([A-Z0-9-]+)"
                ],
                "vendor_name": [
                    r"(?:from|vendor|company):\s*(.+?)(?:\n|$)",
                    r"^([A-Z][A-Za-z\s&.,]+?)(?:\n|\s{2,})",
                ],
                "total_amount": [
                    r"total\s*amount?:?\s*\$?(\d+[.,]\d{2})",
                    r"total:?\s*\$?(\d+[.,]\d{2})",
                    r"amount\s*due:?\s*\$?(\d+[.,]\d{2})"
                ],
                "date": [
                    r"date:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                    r"invoice\s*date:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                    r"(\d{4}-\d{1,2}-\d{1,2})"
                ],
                "due_date": [
                    r"due\s*date:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                    r"payment\s*due:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
                ]
            },
            "receipt": {
                "merchant_name": [
                    r"^([A-Z][A-Za-z\s&.,]+?)(?:\n|\s{2,})",
                    r"thank\s*you\s*for\s*shopping\s*at\s*(.+?)(?:\n|$)"
                ],
                "receipt_number": [
                    r"receipt\s*#?:?\s*([A-Z0-9-]+)",
                    r"transaction\s*#?:?\s*([A-Z0-9-]+)"
                ],
                "total_amount": [
                    r"total:?\s*\$?(\d+[.,]\d{2})",
                    r"amount:?\s*\$?(\d+[.,]\d{2})"
                ],
                "date": [
                    r"date:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                    r"(\d{4}-\d{1,2}-\d{1,2})"
                ],
                "payment_method": [
                    r"(cash|credit|debit|card|visa|mastercard|amex)",
                    r"payment\s*method:?\s*(.+?)(?:\n|$)"
                ]
            },
            "contract": {
                "contract_title": [
                    r"^(.+?(?:contract|agreement))",
                    r"(?:contract|agreement)\s*title:?\s*(.+?)(?:\n|$)"
                ],
                "parties": [
                    r"between\s*(.+?)\s*and\s*(.+?)(?:\n|$)",
                    r"party\s*1:?\s*(.+?)(?:\n|$)",
                    r"party\s*2:?\s*(.+?)(?:\n|$)"
                ],
                "effective_date": [
                    r"effective\s*date:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                    r"date\s*of\s*agreement:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
                ],
                "terms": [
                    r"terms?\s*and\s*conditions?:?\s*(.+?)(?:\n\n|$)",
                    r"agreement\s*terms:?\s*(.+?)(?:\n\n|$)"
                ]
            },
            "form": {
                "form_title": [
                    r"^(.+?(?:form|application))",
                    r"(?:form|application)\s*title:?\s*(.+?)(?:\n|$)"
                ],
                "name_field": [
                    r"name:?\s*(.+?)(?:\n|$)",
                    r"full\s*name:?\s*(.+?)(?:\n|$)"
                ],
                "date_field": [
                    r"date:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                    r"today'?s?\s*date:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
                ]
            }
        }
        
        # Data validation patterns
        self.validation_patterns = {
            "amount": r"^\$?(\d+(?:[.,]\d{2})?)\$?$",
            "date": r"^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$|^\d{4}-\d{1,2}-\d{1,2}$",
            "phone": r"^[\+]?[1-9]?[\d\s\-\(\)]{10,15}$",
            "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        }
        
        self.status = "active"
        logger.info("ContentAnalysisAgent initialized with extraction patterns")
    
    async def process(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze extracted content and structure data
        
        Args:
            document_data: Contains OCR results and classification data
            
        Returns:
            Structured content analysis with extracted fields
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            if not await self.validate_input(document_data):
                raise ValueError("Invalid input data for content analysis")
            
            document_id = document_data["document_id"]
            ocr_result = document_data.get("ocr_result", {})
            classification = document_data.get("classification", {})
            
            logger.info(f"Analyzing content for document {document_id}")
            
            # Extract basic information
            extracted_text = ocr_result.get("extracted_text", "")
            document_type = classification.get("document_type", "unknown")
            confidence = classification.get("confidence", 0.0)
            
            # Step 1: Text preprocessing
            processed_text = await self._preprocess_text(extracted_text)
            
            # Step 2: Extract structured fields
            extracted_fields = await self._extract_fields(processed_text, document_type)
            
            # Step 3: Validate extracted data
            validated_fields = await self._validate_fields(extracted_fields, document_type)
            
            # Step 4: Detect tables and lists
            structured_elements = await self._detect_structured_elements(processed_text)
            
            # Step 5: Calculate content confidence
            content_confidence = await self._calculate_content_confidence(
                validated_fields, structured_elements, ocr_result
            )
            
            # Step 6: Generate content summary
            content_summary = await self._generate_content_summary(
                processed_text, validated_fields, document_type
            )
            
            processing_time = asyncio.get_event_loop().time() - start_time
            self.update_metrics(True, processing_time)
            
            result = {
                "success": True,
                "document_id": document_id,
                "content_analysis": {
                    "document_type": document_type,
                    "extracted_fields": validated_fields,
                    "structured_elements": structured_elements,
                    "content_summary": content_summary,
                    "confidence_scores": content_confidence,
                    "processing_metadata": {
                        "text_length": len(processed_text),
                        "fields_extracted": len(validated_fields),
                        "validation_passed": all(f.get("valid", False) for f in validated_fields.values())
                    }
                },
                "processing_time": processing_time,
                "agent": self.name,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Content analysis completed for document {document_id}")
            return result
            
        except Exception as e:
            processing_time = asyncio.get_event_loop().time() - start_time
            self.update_metrics(False, processing_time)
            return await self.handle_error(e, document_data.get("document_id", "unknown"))
    
    async def _preprocess_text(self, text: str) -> str:
        """Clean and normalize text for better extraction"""
        if not text:
            return ""
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove extra newlines but preserve structure
        text = re.sub(r'\n\s*\n', '\n', text)
        
        # Normalize currency symbols
        text = re.sub(r'[\$\€\£\¥]', '$', text)
        
        # Normalize date separators
        text = re.sub(r'(\d{1,2})[./](\d{1,2})[./](\d{2,4})', r'\1/\2/\3', text)
        
        return text.strip()
    
    async def _extract_fields(self, text: str, document_type: str) -> Dict[str, Any]:
        """Extract structured fields based on document type"""
        extracted_fields = {}
        
        if document_type not in self.extraction_patterns:
            logger.warning(f"No extraction patterns for document type: {document_type}")
            return extracted_fields
        
        patterns = self.extraction_patterns[document_type]
        
        for field_name, field_patterns in patterns.items():
            extracted_value = None
            
            # Try each pattern until we find a match
            for pattern in field_patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    if match.groups():
                        extracted_value = match.group(1).strip()
                    else:
                        extracted_value = match.group(0).strip()
                    break
            
            if extracted_value:
                extracted_fields[field_name] = {
                    "value": extracted_value,
                    "raw_value": extracted_value,
                    "confidence": 0.8,  # Base confidence
                    "extraction_method": "regex_pattern"
                }
        
        return extracted_fields
    
    async def _validate_fields(self, fields: Dict[str, Any], document_type: str) -> Dict[str, Any]:
        """Validate and normalize extracted fields"""
        validated_fields = {}
        
        for field_name, field_data in fields.items():
            raw_value = field_data.get("value", "")
            
            # Apply field-specific validation
            validated_value, is_valid, normalized_value = await self._validate_single_field(
                field_name, raw_value, document_type
            )
            
            validated_fields[field_name] = {
                "value": validated_value,
                "normalized_value": normalized_value,
                "raw_value": raw_value,
                "valid": is_valid,
                "confidence": field_data.get("confidence", 0.8) * (1.0 if is_valid else 0.5),
                "validation_method": "pattern_validation",
                "field_type": self._get_field_type(field_name)
            }
        
        return validated_fields
    
    async def _validate_single_field(self, field_name: str, value: str, document_type: str) -> tuple:
        """Validate a single field value"""
        if not value:
            return value, False, value
        
        # Amount validation
        if "amount" in field_name.lower() or "total" in field_name.lower():
            amount_match = re.match(self.validation_patterns["amount"], value)
            if amount_match:
                normalized = float(amount_match.group(1).replace(',', '.'))
                return value, True, normalized
            return value, False, value
        
        # Date validation
        if "date" in field_name.lower():
            date_match = re.match(self.validation_patterns["date"], value)
            if date_match:
                try:
                    # Attempt to parse the date
                    normalized = self._parse_date(value)
                    return value, True, normalized
                except:
                    return value, False, value
            return value, False, value
        
        # Phone validation
        if "phone" in field_name.lower():
            phone_match = re.match(self.validation_patterns["phone"], value)
            return value, bool(phone_match), value
        
        # Email validation
        if "email" in field_name.lower():
            email_match = re.match(self.validation_patterns["email"], value)
            return value, bool(email_match), value
        
        # Default validation (non-empty string)
        return value, len(value.strip()) > 0, value.strip()
    
    def _parse_date(self, date_str: str) -> str:
        """Parse and normalize date string"""
        # Try different date formats
        formats = ["%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d", "%m-%d-%Y"]
        
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                return parsed_date.strftime("%Y-%m-%d")
            except ValueError:
                continue
        
        raise ValueError(f"Could not parse date: {date_str}")
    
    def _get_field_type(self, field_name: str) -> str:
        """Determine field type based on field name"""
        if any(term in field_name.lower() for term in ["amount", "total", "price", "cost"]):
            return "currency"
        elif "date" in field_name.lower():
            return "date"
        elif any(term in field_name.lower() for term in ["phone", "tel"]):
            return "phone"
        elif "email" in field_name.lower():
            return "email"
        elif any(term in field_name.lower() for term in ["number", "id", "#"]):
            return "identifier"
        else:
            return "text"
    
    async def _detect_structured_elements(self, text: str) -> Dict[str, Any]:
        """Detect tables, lists, and other structured elements"""
        elements = {
            "tables": [],
            "lists": [],
            "sections": []
        }
        
        # Detect table-like structures
        lines = text.split('\n')
        potential_tables = []
        
        for i, line in enumerate(lines):
            # Look for lines with multiple numeric values or consistent spacing
            if re.search(r'\$?\d+[.,]\d{2}.*\$?\d+[.,]\d{2}', line):
                potential_tables.append({
                    "line_number": i,
                    "content": line.strip(),
                    "type": "table_row"
                })
        
        if potential_tables:
            elements["tables"] = potential_tables
        
        # Detect bullet points or numbered lists
        list_items = []
        for i, line in enumerate(lines):
            if re.match(r'^\s*[-*•]\s+', line) or re.match(r'^\s*\d+[.)]\s+', line):
                list_items.append({
                    "line_number": i,
                    "content": line.strip(),
                    "type": "list_item"
                })
        
        if list_items:
            elements["lists"] = list_items
        
        return elements
    
    async def _calculate_content_confidence(self, fields: Dict[str, Any], elements: Dict[str, Any], ocr_result: Dict[str, Any]) -> Dict[str, float]:
        """Calculate confidence scores for different aspects of content analysis"""
        confidence_scores = {
            "overall": 0.0,
            "field_extraction": 0.0,
            "data_validation": 0.0,
            "structure_detection": 0.0
        }
        
        # Field extraction confidence
        if fields:
            field_confidences = [f.get("confidence", 0.0) for f in fields.values()]
            confidence_scores["field_extraction"] = sum(field_confidences) / len(field_confidences)
        
        # Data validation confidence
        if fields:
            valid_fields = [f for f in fields.values() if f.get("valid", False)]
            confidence_scores["data_validation"] = len(valid_fields) / len(fields) if fields else 0.0
        
        # Structure detection confidence
        structure_count = len(elements.get("tables", [])) + len(elements.get("lists", []))
        confidence_scores["structure_detection"] = min(structure_count * 0.2, 1.0)
        
        # OCR confidence
        ocr_confidence = ocr_result.get("confidence", 0.0)
        
        # Overall confidence (weighted average)
        confidence_scores["overall"] = (
            confidence_scores["field_extraction"] * 0.4 +
            confidence_scores["data_validation"] * 0.3 +
            confidence_scores["structure_detection"] * 0.1 +
            ocr_confidence * 0.2
        )
        
        return confidence_scores
    
    async def _generate_content_summary(self, text: str, fields: Dict[str, Any], document_type: str) -> Dict[str, Any]:
        """Generate a summary of the document content"""
        summary = {
            "document_type": document_type,
            "key_information": {},
            "statistics": {
                "text_length": len(text),
                "word_count": len(text.split()),
                "line_count": len(text.split('\n')),
                "fields_extracted": len(fields)
            },
            "quality_assessment": "good"  # good, fair, poor
        }
        
        # Extract key information based on document type
        if document_type == "invoice":
            summary["key_information"] = {
                "vendor": fields.get("vendor_name", {}).get("value", "Not found"),
                "invoice_number": fields.get("invoice_number", {}).get("value", "Not found"),
                "total": fields.get("total_amount", {}).get("value", "Not found"),
                "date": fields.get("date", {}).get("value", "Not found")
            }
        
        elif document_type == "receipt":
            summary["key_information"] = {
                "merchant": fields.get("merchant_name", {}).get("value", "Not found"),
                "total": fields.get("total_amount", {}).get("value", "Not found"),
                "date": fields.get("date", {}).get("value", "Not found")
            }
        
        # Quality assessment based on field extraction success
        valid_fields = sum(1 for f in fields.values() if f.get("valid", False))
        total_fields = len(fields) if fields else 1
        
        success_rate = valid_fields / total_fields
        if success_rate >= 0.8:
            summary["quality_assessment"] = "excellent"
        elif success_rate >= 0.6:
            summary["quality_assessment"] = "good"
        elif success_rate >= 0.4:
            summary["quality_assessment"] = "fair"
        else:
            summary["quality_assessment"] = "poor"
        
        return summary