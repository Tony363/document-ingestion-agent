"""
Schema Generation Agent

Generates JSON schemas from extracted data that can be used
to trigger webhooks and API automations.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import uuid
from pydantic import BaseModel, Field

from .base_agent import BaseAgent, AgentContext
from .content_analysis_agent import ExtractedField, ExtractedTable

class SchemaInput(BaseModel):
    """Input for schema generation"""
    document_type: str
    extracted_data: Dict[str, Any]
    fields: Optional[List[ExtractedField]] = None
    tables: Optional[List[ExtractedTable]] = None

class WebhookTrigger(BaseModel):
    """Webhook trigger configuration"""
    trigger_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action: str  # "webhook", "api_call", "email", "database"
    endpoint: Optional[str] = None
    method: str = "POST"
    headers: Dict[str, str] = Field(default_factory=dict)
    condition: Optional[Dict[str, Any]] = None
    payload_template: Optional[Dict[str, Any]] = None

class DocumentSchema(BaseModel):
    """Generated document schema"""
    schema_version: str = "1.0"
    schema_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    document_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    confidence_score: float
    
    # Extracted structured data
    extracted_data: Dict[str, Any]
    
    # Processing metadata
    processing_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Automation triggers
    automation_triggers: List[WebhookTrigger] = Field(default_factory=list)
    
    # Validation status
    validation_status: str = "pending"
    validation_errors: List[str] = Field(default_factory=list)

class SchemaGenerationAgent(BaseAgent[SchemaInput, DocumentSchema]):
    """
    Agent for generating JSON schemas from extracted document data
    """
    
    # Template mappings for different document types
    SCHEMA_TEMPLATES = {
        "invoice": {
            "required_fields": ["invoice_number", "vendor_name", "total_amount"],
            "optional_fields": ["invoice_date", "due_date", "po_number", "line_items"],
            "triggers": [
                {
                    "action": "webhook",
                    "condition": {"total_amount": {"$gte": 1000}},
                    "endpoint": "/api/invoices/high-value"
                },
                {
                    "action": "webhook",
                    "condition": {"due_date": {"$exists": True}},
                    "endpoint": "/api/invoices/payable"
                }
            ]
        },
        "receipt": {
            "required_fields": ["merchant_name", "total_amount", "transaction_date"],
            "optional_fields": ["receipt_number", "payment_method", "items"],
            "triggers": [
                {
                    "action": "webhook",
                    "endpoint": "/api/receipts/process"
                }
            ]
        },
        "contract": {
            "required_fields": ["party1", "party2", "effective_date"],
            "optional_fields": ["end_date", "contract_value", "terms"],
            "triggers": [
                {
                    "action": "webhook",
                    "endpoint": "/api/contracts/new"
                },
                {
                    "action": "email",
                    "condition": {"end_date": {"$exists": True}},
                    "endpoint": "legal@company.com"
                }
            ]
        },
        "form": {
            "required_fields": [],
            "optional_fields": ["email", "phone", "name"],
            "triggers": [
                {
                    "action": "webhook",
                    "endpoint": "/api/forms/submission"
                }
            ]
        }
    }
    
    def __init__(self):
        super().__init__(
            name="schema_generation_agent",
            max_retries=2,
            timeout=20.0
        )
        
    async def validate_input(self, input_data: SchemaInput) -> bool:
        """Validate schema generation input"""
        if not input_data.document_type:
            return False
        return True
    
    async def process(
        self,
        input_data: SchemaInput,
        context: AgentContext
    ) -> DocumentSchema:
        """
        Generate JSON schema from extracted data
        
        Args:
            input_data: Schema input with extracted data
            context: Agent execution context
            
        Returns:
            Generated document schema
        """
        # Build extracted data structure
        extracted_data = await self._build_extracted_data(input_data)
        
        # Generate automation triggers based on document type
        triggers = await self._generate_triggers(
            input_data.document_type,
            extracted_data
        )
        
        # Calculate confidence score
        confidence_score = await self._calculate_confidence(
            input_data,
            extracted_data
        )
        
        # Build processing metadata
        processing_metadata = {
            "ocr_confidence": input_data.extracted_data.get("ocr_confidence", 0.0),
            "extraction_method": input_data.extracted_data.get("extraction_method", "automatic"),
            "processing_time_ms": input_data.extracted_data.get("processing_time_ms", 0),
            "page_count": input_data.extracted_data.get("page_count", 1),
            "has_tables": len(input_data.tables) > 0 if input_data.tables else False,
            "field_count": len(input_data.fields) if input_data.fields else 0
        }
        
        # Create document schema
        schema = DocumentSchema(
            document_id=context.document_id,
            document_type=input_data.document_type,
            confidence_score=confidence_score,
            extracted_data=extracted_data,
            processing_metadata=processing_metadata,
            automation_triggers=triggers
        )
        
        return schema
    
    async def _build_extracted_data(self, input_data: SchemaInput) -> Dict[str, Any]:
        """
        Build structured extracted data from fields and tables
        
        Args:
            input_data: Input with extracted fields and tables
            
        Returns:
            Structured data dictionary
        """
        extracted = {
            "document_type": input_data.document_type,
            "metadata": {},
            "fields": {},
            "tables": [],
            "raw_data": input_data.extracted_data
        }
        
        # Process fields
        if input_data.fields:
            for field in input_data.fields:
                # Group related fields
                if field.name in ["invoice_number", "receipt_number", "po_number"]:
                    extracted["metadata"][field.name] = field.value
                else:
                    extracted["fields"][field.name] = {
                        "value": field.value,
                        "confidence": field.confidence
                    }
        
        # Process tables
        if input_data.tables:
            for table in input_data.tables:
                extracted["tables"].append({
                    "headers": table.headers,
                    "rows": table.rows,
                    "row_count": len(table.rows),
                    "confidence": table.confidence
                })
        
        # Add document-specific structures
        if input_data.document_type == "invoice":
            extracted = await self._structure_invoice_data(extracted)
        elif input_data.document_type == "receipt":
            extracted = await self._structure_receipt_data(extracted)
        elif input_data.document_type == "contract":
            extracted = await self._structure_contract_data(extracted)
        
        return extracted
    
    async def _structure_invoice_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Structure invoice-specific data"""
        invoice_structure = {
            "invoice_details": {
                "number": data.get("metadata", {}).get("invoice_number"),
                "date": data.get("fields", {}).get("invoice_date", {}).get("value"),
                "due_date": data.get("fields", {}).get("due_date", {}).get("value"),
                "po_number": data.get("metadata", {}).get("po_number")
            },
            "vendor": {
                "name": data.get("fields", {}).get("vendor_name", {}).get("value"),
                "tax_id": data.get("fields", {}).get("tax_id", {}).get("value")
            },
            "amounts": {
                "subtotal": data.get("fields", {}).get("subtotal", {}).get("value"),
                "tax": data.get("fields", {}).get("tax_amount", {}).get("value"),
                "total": data.get("fields", {}).get("total_amount", {}).get("value")
            },
            "line_items": data.get("tables", [{}])[0].get("rows", []) if data.get("tables") else []
        }
        
        data["structured"] = invoice_structure
        return data
    
    async def _structure_receipt_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Structure receipt-specific data"""
        receipt_structure = {
            "transaction": {
                "number": data.get("metadata", {}).get("receipt_number"),
                "date": data.get("fields", {}).get("transaction_date", {}).get("value"),
                "merchant": data.get("fields", {}).get("merchant_name", {}).get("value")
            },
            "payment": {
                "method": data.get("fields", {}).get("payment_method", {}).get("value"),
                "total": data.get("fields", {}).get("total_amount", {}).get("value")
            },
            "items": data.get("tables", [{}])[0].get("rows", []) if data.get("tables") else []
        }
        
        data["structured"] = receipt_structure
        return data
    
    async def _structure_contract_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Structure contract-specific data"""
        contract_structure = {
            "parties": {
                "party1": data.get("fields", {}).get("party1", {}).get("value"),
                "party2": data.get("fields", {}).get("party2", {}).get("value")
            },
            "dates": {
                "effective": data.get("fields", {}).get("effective_date", {}).get("value"),
                "termination": data.get("fields", {}).get("end_date", {}).get("value")
            },
            "terms": {
                "value": data.get("fields", {}).get("contract_value", {}).get("value")
            }
        }
        
        data["structured"] = contract_structure
        return data
    
    async def _generate_triggers(
        self,
        document_type: str,
        extracted_data: Dict[str, Any]
    ) -> List[WebhookTrigger]:
        """
        Generate automation triggers based on document type and data
        
        Args:
            document_type: Type of document
            extracted_data: Extracted data structure
            
        Returns:
            List of webhook triggers
        """
        triggers = []
        
        # Get template triggers for document type
        template = self.SCHEMA_TEMPLATES.get(document_type, {})
        template_triggers = template.get("triggers", [])
        
        for trigger_template in template_triggers:
            # Check if condition is met
            condition = trigger_template.get("condition")
            if condition:
                if not await self._evaluate_condition(condition, extracted_data):
                    continue
            
            # Create trigger
            trigger = WebhookTrigger(
                action=trigger_template.get("action", "webhook"),
                endpoint=trigger_template.get("endpoint"),
                method=trigger_template.get("method", "POST"),
                condition=condition,
                payload_template={
                    "document_id": extracted_data.get("document_id"),
                    "document_type": document_type,
                    "data": extracted_data.get("structured", extracted_data)
                }
            )
            
            triggers.append(trigger)
        
        # Add default trigger if no triggers generated
        if not triggers:
            triggers.append(WebhookTrigger(
                action="webhook",
                endpoint=f"/api/documents/{document_type}",
                payload_template={
                    "document_type": document_type,
                    "data": extracted_data
                }
            ))
        
        return triggers
    
    async def _evaluate_condition(
        self,
        condition: Dict[str, Any],
        data: Dict[str, Any]
    ) -> bool:
        """
        Evaluate trigger condition against data
        
        Args:
            condition: Condition to evaluate
            data: Data to check against
            
        Returns:
            True if condition is met
        """
        # Simple condition evaluation
        # In production, use a proper expression evaluator
        for field, constraint in condition.items():
            field_value = data.get("fields", {}).get(field, {}).get("value")
            
            if isinstance(constraint, dict):
                if "$exists" in constraint:
                    if constraint["$exists"] and field_value is None:
                        return False
                    elif not constraint["$exists"] and field_value is not None:
                        return False
                
                if "$gte" in constraint and field_value:
                    try:
                        if float(field_value) < float(constraint["$gte"]):
                            return False
                    except:
                        return False
                
                if "$lte" in constraint and field_value:
                    try:
                        if float(field_value) > float(constraint["$lte"]):
                            return False
                    except:
                        return False
            else:
                if field_value != constraint:
                    return False
        
        return True
    
    async def _calculate_confidence(
        self,
        input_data: SchemaInput,
        extracted_data: Dict[str, Any]
    ) -> float:
        """
        Calculate overall schema confidence
        
        Args:
            input_data: Input data with confidence scores
            extracted_data: Extracted data structure
            
        Returns:
            Overall confidence score
        """
        confidence_scores = []
        
        # Add field confidences
        if input_data.fields:
            for field in input_data.fields:
                confidence_scores.append(field.confidence)
        
        # Add table confidences
        if input_data.tables:
            for table in input_data.tables:
                confidence_scores.append(table.confidence)
        
        # Add base confidence for document type
        template = self.SCHEMA_TEMPLATES.get(input_data.document_type)
        if template:
            # Check if required fields are present
            required_fields = template.get("required_fields", [])
            present_fields = set(extracted_data.get("fields", {}).keys())
            
            if required_fields:
                completeness = len(present_fields.intersection(required_fields)) / len(required_fields)
                confidence_scores.append(completeness)
        
        # Calculate average confidence
        if confidence_scores:
            return sum(confidence_scores) / len(confidence_scores)
        
        return 0.5  # Default confidence