"""
Schema Generation Agent - Dynamic JSON schema creation
Generates structured JSON schemas based on extracted content and document type
"""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class SchemaGenerationAgent(BaseAgent):
    """Agent responsible for generating dynamic JSON schemas"""
    
    def __init__(self):
        super().__init__("schema_generation_agent", "1.0.0")
        
        # Base schema templates for different document types
        self.schema_templates = {
            "invoice": {
                "type": "object",
                "required": ["document_type", "extraction_confidence", "content", "metadata"],
                "properties": {
                    "document_type": {"type": "string", "const": "invoice"},
                    "extraction_confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    "content": {
                        "type": "object",
                        "required": ["vendor_info", "invoice_details"],
                        "properties": {
                            "vendor_info": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "address": {"type": "string"},
                                    "tax_id": {"type": "string"},
                                    "phone": {"type": "string"},
                                    "email": {"type": "string"}
                                }
                            },
                            "invoice_details": {
                                "type": "object",
                                "properties": {
                                    "invoice_number": {"type": "string"},
                                    "date": {"type": "string", "format": "date"},
                                    "due_date": {"type": "string", "format": "date"},
                                    "po_number": {"type": "string"}
                                }
                            },
                            "line_items": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "description": {"type": "string"},
                                        "quantity": {"type": "number"},
                                        "unit_price": {"type": "number"},
                                        "total": {"type": "number"}
                                    }
                                }
                            },
                            "totals": {
                                "type": "object",
                                "properties": {
                                    "subtotal": {"type": "number"},
                                    "tax": {"type": "number"},
                                    "total": {"type": "number"},
                                    "currency": {"type": "string", "default": "USD"}
                                }
                            }
                        }
                    },
                    "metadata": {
                        "type": "object",
                        "properties": {
                            "pages": {"type": "integer"},
                            "processing_time": {"type": "number"},
                            "language": {"type": "string"},
                            "ocr_confidence": {"type": "number"}
                        }
                    },
                    "webhook_ready": {"type": "boolean"}
                }
            },
            
            "receipt": {
                "type": "object",
                "required": ["document_type", "extraction_confidence", "content"],
                "properties": {
                    "document_type": {"type": "string", "const": "receipt"},
                    "extraction_confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    "content": {
                        "type": "object",
                        "required": ["merchant_info", "transaction_details"],
                        "properties": {
                            "merchant_info": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "address": {"type": "string"},
                                    "phone": {"type": "string"}
                                }
                            },
                            "transaction_details": {
                                "type": "object",
                                "properties": {
                                    "receipt_number": {"type": "string"},
                                    "date": {"type": "string", "format": "date"},
                                    "time": {"type": "string", "format": "time"}
                                }
                            },
                            "items": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "quantity": {"type": "number"},
                                        "price": {"type": "number"}
                                    }
                                }
                            },
                            "payment": {
                                "type": "object",
                                "properties": {
                                    "method": {"type": "string"},
                                    "total": {"type": "number"},
                                    "tax": {"type": "number"},
                                    "currency": {"type": "string", "default": "USD"}
                                }
                            }
                        }
                    },
                    "webhook_ready": {"type": "boolean"}
                }
            },
            
            "contract": {
                "type": "object",
                "required": ["document_type", "extraction_confidence", "content"],
                "properties": {
                    "document_type": {"type": "string", "const": "contract"},
                    "extraction_confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    "content": {
                        "type": "object",
                        "properties": {
                            "contract_info": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "type": {"type": "string"},
                                    "effective_date": {"type": "string", "format": "date"},
                                    "expiration_date": {"type": "string", "format": "date"}
                                }
                            },
                            "parties": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "role": {"type": "string"},
                                        "address": {"type": "string"}
                                    }
                                }
                            },
                            "terms": {
                                "type": "object",
                                "properties": {
                                    "summary": {"type": "string"},
                                    "key_clauses": {"type": "array", "items": {"type": "string"}}
                                }
                            }
                        }
                    },
                    "webhook_ready": {"type": "boolean"}
                }
            },
            
            "form": {
                "type": "object",
                "required": ["document_type", "extraction_confidence", "content"],
                "properties": {
                    "document_type": {"type": "string", "const": "form"},
                    "extraction_confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    "content": {
                        "type": "object",
                        "properties": {
                            "form_info": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "type": {"type": "string"},
                                    "date": {"type": "string", "format": "date"}
                                }
                            },
                            "fields": {
                                "type": "object",
                                "additionalProperties": {
                                    "type": "object",
                                    "properties": {
                                        "value": {"type": "string"},
                                        "field_type": {"type": "string"},
                                        "required": {"type": "boolean"}
                                    }
                                }
                            }
                        }
                    },
                    "webhook_ready": {"type": "boolean"}
                }
            }
        }
        
        # Schema version tracking
        self.schema_version = "1.0"
        
        self.status = "active"
        logger.info("SchemaGenerationAgent initialized with templates for 4 document types")
    
    async def process(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate JSON schema based on content analysis
        
        Args:
            document_data: Contains content analysis results and classification
            
        Returns:
            Generated JSON schema ready for webhook delivery
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            if not await self.validate_input(document_data):
                raise ValueError("Invalid input data for schema generation")
            
            document_id = document_data["document_id"]
            content_analysis = document_data.get("content_analysis", {})
            classification = document_data.get("classification", {})
            ocr_result = document_data.get("ocr_result", {})
            
            logger.info(f"Generating schema for document {document_id}")
            
            # Extract key information
            document_type = classification.get("document_type", "unknown")
            extracted_fields = content_analysis.get("extracted_fields", {})
            confidence_scores = content_analysis.get("confidence_scores", {})
            
            # Step 1: Select base template
            base_template = await self._select_base_template(document_type)
            
            # Step 2: Generate schema data
            schema_data = await self._generate_schema_data(
                document_type, extracted_fields, content_analysis, ocr_result
            )
            
            # Step 3: Validate schema against template
            validation_result = await self._validate_schema_data(schema_data, base_template)
            
            # Step 4: Enhance schema with metadata
            enhanced_schema = await self._enhance_schema(
                schema_data, validation_result, document_data
            )
            
            # Step 5: Determine webhook readiness
            webhook_ready = await self._assess_webhook_readiness(
                enhanced_schema, confidence_scores, validation_result
            )
            
            processing_time = asyncio.get_event_loop().time() - start_time
            self.update_metrics(True, processing_time)
            
            result = {
                "success": True,
                "document_id": document_id,
                "generated_schema": {
                    "schema_version": self.schema_version,
                    "document_type": document_type,
                    "data": enhanced_schema,
                    "webhook_ready": webhook_ready,
                    "validation": validation_result,
                    "template_used": document_type,
                    "generation_metadata": {
                        "fields_mapped": len(extracted_fields),
                        "confidence_threshold_met": confidence_scores.get("overall", 0.0) >= 0.7,
                        "required_fields_present": validation_result.get("required_fields_valid", False)
                    }
                },
                "processing_time": processing_time,
                "agent": self.name,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Schema generation completed for document {document_id} (webhook_ready: {webhook_ready})")
            return result
            
        except Exception as e:
            processing_time = asyncio.get_event_loop().time() - start_time
            self.update_metrics(False, processing_time)
            return await self.handle_error(e, document_data.get("document_id", "unknown"))
    
    async def _select_base_template(self, document_type: str) -> Dict[str, Any]:
        """Select appropriate schema template based on document type"""
        if document_type in self.schema_templates:
            return self.schema_templates[document_type].copy()
        else:
            logger.warning(f"No template found for document type: {document_type}, using generic")
            return self._create_generic_template()
    
    def _create_generic_template(self) -> Dict[str, Any]:
        """Create a generic schema template for unknown document types"""
        return {
            "type": "object",
            "required": ["document_type", "extraction_confidence", "content"],
            "properties": {
                "document_type": {"type": "string"},
                "extraction_confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "content": {
                    "type": "object",
                    "additionalProperties": True
                },
                "webhook_ready": {"type": "boolean"}
            }
        }
    
    async def _generate_schema_data(self, document_type: str, extracted_fields: Dict[str, Any], 
                                   content_analysis: Dict[str, Any], ocr_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate the actual schema data based on extracted content"""
        
        # Base schema structure
        schema_data = {
            "document_type": document_type,
            "extraction_confidence": content_analysis.get("confidence_scores", {}).get("overall", 0.0),
            "content": {},
            "metadata": {
                "pages": ocr_result.get("page_count", 1),
                "processing_time": content_analysis.get("processing_time", 0.0),
                "language": ocr_result.get("language", "en"),
                "ocr_confidence": ocr_result.get("confidence", 0.0)
            },
            "webhook_ready": False  # Will be determined later
        }
        
        # Document type specific content mapping
        if document_type == "invoice":
            schema_data["content"] = await self._map_invoice_content(extracted_fields, content_analysis)
        elif document_type == "receipt":
            schema_data["content"] = await self._map_receipt_content(extracted_fields, content_analysis)
        elif document_type == "contract":
            schema_data["content"] = await self._map_contract_content(extracted_fields, content_analysis)
        elif document_type == "form":
            schema_data["content"] = await self._map_form_content(extracted_fields, content_analysis)
        else:
            schema_data["content"] = await self._map_generic_content(extracted_fields, content_analysis)
        
        return schema_data
    
    async def _map_invoice_content(self, fields: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Map extracted fields to invoice schema structure"""
        content = {
            "vendor_info": {},
            "invoice_details": {},
            "line_items": [],
            "totals": {}
        }
        
        # Map vendor information
        if "vendor_name" in fields:
            content["vendor_info"]["name"] = fields["vendor_name"]["value"]
        
        # Map invoice details
        field_mapping = {
            "invoice_number": "invoice_number",
            "date": "date",
            "due_date": "due_date"
        }
        
        for field_key, schema_key in field_mapping.items():
            if field_key in fields and fields[field_key]["valid"]:
                content["invoice_details"][schema_key] = fields[field_key]["normalized_value"] or fields[field_key]["value"]
        
        # Map totals
        if "total_amount" in fields and fields["total_amount"]["valid"]:
            total_value = fields["total_amount"]["normalized_value"] or 0.0
            content["totals"] = {
                "total": total_value,
                "currency": "USD"
            }
        
        # Extract line items from structured elements (simplified)
        structured_elements = analysis.get("structured_elements", {})
        tables = structured_elements.get("tables", [])
        if tables:
            content["line_items"] = [
                {
                    "description": "Extracted item",
                    "total": self._extract_amount_from_line(table.get("content", ""))
                }
                for table in tables[:5]  # Limit to 5 items
            ]
        
        return content
    
    async def _map_receipt_content(self, fields: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Map extracted fields to receipt schema structure"""
        content = {
            "merchant_info": {},
            "transaction_details": {},
            "items": [],
            "payment": {}
        }
        
        # Map merchant information
        if "merchant_name" in fields:
            content["merchant_info"]["name"] = fields["merchant_name"]["value"]
        
        # Map transaction details
        field_mapping = {
            "receipt_number": "receipt_number",
            "date": "date"
        }
        
        for field_key, schema_key in field_mapping.items():
            if field_key in fields and fields[field_key]["valid"]:
                content["transaction_details"][schema_key] = fields[field_key]["normalized_value"] or fields[field_key]["value"]
        
        # Map payment information
        if "total_amount" in fields and fields["total_amount"]["valid"]:
            total_value = fields["total_amount"]["normalized_value"] or 0.0
            content["payment"]["total"] = total_value
            content["payment"]["currency"] = "USD"
        
        if "payment_method" in fields:
            content["payment"]["method"] = fields["payment_method"]["value"]
        
        return content
    
    async def _map_contract_content(self, fields: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Map extracted fields to contract schema structure"""
        content = {
            "contract_info": {},
            "parties": [],
            "terms": {}
        }
        
        # Map contract information
        if "contract_title" in fields:
            content["contract_info"]["title"] = fields["contract_title"]["value"]
        
        if "effective_date" in fields and fields["effective_date"]["valid"]:
            content["contract_info"]["effective_date"] = fields["effective_date"]["normalized_value"]
        
        # Map parties (simplified)
        if "parties" in fields:
            content["parties"] = [
                {"name": fields["parties"]["value"], "role": "party"}
            ]
        
        # Map terms
        if "terms" in fields:
            content["terms"]["summary"] = fields["terms"]["value"]
        
        return content
    
    async def _map_form_content(self, fields: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Map extracted fields to form schema structure"""
        content = {
            "form_info": {},
            "fields": {}
        }
        
        # Map form information
        if "form_title" in fields:
            content["form_info"]["title"] = fields["form_title"]["value"]
        
        if "date_field" in fields and fields["date_field"]["valid"]:
            content["form_info"]["date"] = fields["date_field"]["normalized_value"]
        
        # Map all other fields
        for field_name, field_data in fields.items():
            if field_name not in ["form_title", "date_field"]:
                content["fields"][field_name] = {
                    "value": field_data["value"],
                    "field_type": field_data.get("field_type", "text"),
                    "required": field_data.get("valid", False)
                }
        
        return content
    
    async def _map_generic_content(self, fields: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Map extracted fields to generic content structure"""
        content = {}
        
        for field_name, field_data in fields.items():
            content[field_name] = {
                "value": field_data["value"],
                "confidence": field_data.get("confidence", 0.0),
                "valid": field_data.get("valid", False)
            }
        
        return content
    
    def _extract_amount_from_line(self, line: str) -> float:
        """Extract monetary amount from a text line"""
        import re
        amount_match = re.search(r'\$?(\d+[.,]\d{2})', line)
        if amount_match:
            return float(amount_match.group(1).replace(',', '.'))
        return 0.0
    
    async def _validate_schema_data(self, schema_data: Dict[str, Any], template: Dict[str, Any]) -> Dict[str, Any]:
        """Validate generated schema data against template"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "required_fields_valid": True,
            "completeness_score": 0.0
        }
        
        try:
            # Check required fields
            required_fields = template.get("required", [])
            missing_required = []
            
            for field in required_fields:
                if field not in schema_data or not schema_data[field]:
                    missing_required.append(field)
            
            if missing_required:
                validation_result["errors"].append(f"Missing required fields: {missing_required}")
                validation_result["required_fields_valid"] = False
                validation_result["valid"] = False
            
            # Calculate completeness score
            total_possible_fields = len(template.get("properties", {}))
            present_fields = len([k for k in schema_data.keys() if schema_data[k]])
            validation_result["completeness_score"] = present_fields / total_possible_fields if total_possible_fields > 0 else 0.0
            
        except Exception as e:
            validation_result["errors"].append(f"Validation error: {str(e)}")
            validation_result["valid"] = False
        
        return validation_result
    
    async def _enhance_schema(self, schema_data: Dict[str, Any], validation: Dict[str, Any], 
                             document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance schema with additional metadata and processing information"""
        enhanced_schema = schema_data.copy()
        
        # Add generation metadata
        enhanced_schema["generation_info"] = {
            "schema_version": self.schema_version,
            "generated_at": datetime.utcnow().isoformat(),
            "agent_version": self.version,
            "validation_passed": validation["valid"],
            "completeness_score": validation["completeness_score"]
        }
        
        # Add processing chain metadata
        enhanced_schema["processing_chain"] = {
            "agents_used": ["validation_agent", "classification_agent", "mistral_ocr_agent", "content_analysis_agent", "schema_generation_agent"],
            "total_processing_time": sum([
                document_data.get("validation_time", 0.0),
                document_data.get("classification_time", 0.0),
                document_data.get("ocr_time", 0.0),
                document_data.get("analysis_time", 0.0)
            ])
        }
        
        return enhanced_schema
    
    async def _assess_webhook_readiness(self, schema_data: Dict[str, Any], confidence_scores: Dict[str, Any], 
                                       validation: Dict[str, Any]) -> bool:
        """Determine if schema is ready for webhook delivery"""
        
        # Criteria for webhook readiness
        criteria = {
            "validation_passed": validation.get("valid", False),
            "confidence_threshold": confidence_scores.get("overall", 0.0) >= 0.7,
            "required_fields_present": validation.get("required_fields_valid", False),
            "completeness_threshold": validation.get("completeness_score", 0.0) >= 0.6
        }
        
        # Log readiness assessment
        logger.info(f"Webhook readiness criteria: {criteria}")
        
        # All criteria must be met
        webhook_ready = all(criteria.values())
        
        # Update schema with readiness status
        schema_data["webhook_ready"] = webhook_ready
        schema_data["readiness_criteria"] = criteria
        
        return webhook_ready
    
    async def get_schema_template(self, document_type: str) -> Optional[Dict[str, Any]]:
        """Get schema template for a specific document type"""
        return self.schema_templates.get(document_type)
    
    async def validate_external_schema(self, schema_data: Dict[str, Any], document_type: str) -> Dict[str, Any]:
        """Validate externally provided schema data"""
        template = await self._select_base_template(document_type)
        return await self._validate_schema_data(schema_data, template)