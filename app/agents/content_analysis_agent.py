"""
Content Analysis Agent

Analyzes extracted text to identify key fields and structured data
based on document type (invoice, receipt, contract, form).
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from .base_agent import BaseAgent, AgentContext

class AnalysisInput(BaseModel):
    """Input for content analysis"""
    extracted_text: str
    document_type: str
    confidence_threshold: float = 0.7

class ExtractedField(BaseModel):
    """Extracted field with confidence"""
    name: str
    value: Any
    confidence: float
    location: Optional[str] = None

class ExtractedTable(BaseModel):
    """Extracted table data"""
    headers: List[str]
    rows: List[Dict[str, Any]]
    confidence: float

class AnalysisOutput(BaseModel):
    """Output from content analysis"""
    document_type: str
    fields: List[ExtractedField]
    tables: List[ExtractedTable]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    extraction_confidence: float

class ContentAnalysisAgent(BaseAgent[AnalysisInput, AnalysisOutput]):
    """
    Agent for analyzing document content and extracting structured data
    """
    
    # Common regex patterns for field extraction
    PATTERNS = {
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "phone": r'[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,5}[-\s\.]?[0-9]{1,5}',
        "date": r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b|\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b',
        "amount": r'\$?\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?',
        "percentage": r'\d+(?:\.\d+)?%',
        "invoice_number": r'(?:invoice|inv|bill)[\s#:]*([A-Z0-9\-]+)',
        "po_number": r'(?:PO|P\.O\.|purchase order)[\s#:]*([A-Z0-9\-]+)',
        "tax_id": r'(?:tax id|ein|tin)[\s:]*([0-9\-]+)',
    }
    
    def __init__(self):
        super().__init__(
            name="content_analysis_agent",
            max_retries=2,
            timeout=30.0
        )
        
    async def validate_input(self, input_data: AnalysisInput) -> bool:
        """Validate analysis input"""
        if not input_data.extracted_text:
            self.logger.warning("No text to analyze")
            return False
        return True
    
    async def process(
        self,
        input_data: AnalysisInput,
        context: AgentContext
    ) -> AnalysisOutput:
        """
        Analyze document content and extract structured data
        
        Args:
            input_data: Analysis input with extracted text
            context: Agent execution context
            
        Returns:
            Structured data extracted from document
        """
        text = input_data.extracted_text
        document_type = input_data.document_type
        
        # Extract fields based on document type
        if document_type == "invoice":
            fields = await self._extract_invoice_fields(text)
        elif document_type == "receipt":
            fields = await self._extract_receipt_fields(text)
        elif document_type == "contract":
            fields = await self._extract_contract_fields(text)
        elif document_type == "form":
            fields = await self._extract_form_fields(text)
        else:
            fields = await self._extract_generic_fields(text)
        
        # Extract tables if present
        tables = await self._extract_tables(text)
        
        # Filter fields by confidence threshold
        filtered_fields = [
            f for f in fields
            if f.confidence >= input_data.confidence_threshold
        ]
        
        # Calculate overall extraction confidence
        extraction_confidence = (
            sum(f.confidence for f in filtered_fields) / len(filtered_fields)
            if filtered_fields else 0.0
        )
        
        return AnalysisOutput(
            document_type=document_type,
            fields=filtered_fields,
            tables=tables,
            metadata={
                "total_fields_extracted": len(fields),
                "fields_above_threshold": len(filtered_fields),
                "has_tables": len(tables) > 0
            },
            extraction_confidence=extraction_confidence
        )
    
    async def _extract_invoice_fields(self, text: str) -> List[ExtractedField]:
        """Extract fields specific to invoices"""
        fields = []
        
        # Invoice number
        invoice_match = re.search(self.PATTERNS["invoice_number"], text, re.IGNORECASE)
        if invoice_match:
            fields.append(ExtractedField(
                name="invoice_number",
                value=invoice_match.group(1),
                confidence=0.9
            ))
        
        # Vendor/Company name (usually at the top)
        lines = text.split('\n')
        if len(lines) > 0:
            # Assume first non-empty line might be company name
            for line in lines[:5]:
                if line.strip() and len(line.strip()) > 3:
                    fields.append(ExtractedField(
                        name="vendor_name",
                        value=line.strip(),
                        confidence=0.7
                    ))
                    break
        
        # Dates
        date_matches = re.findall(self.PATTERNS["date"], text)
        if date_matches:
            fields.append(ExtractedField(
                name="invoice_date",
                value=date_matches[0],
                confidence=0.8
            ))
            if len(date_matches) > 1:
                fields.append(ExtractedField(
                    name="due_date",
                    value=date_matches[1],
                    confidence=0.7
                ))
        
        # Amounts
        amount_matches = re.findall(self.PATTERNS["amount"], text)
        if amount_matches:
            # Look for total amount (usually the largest or last amount)
            amounts = []
            for match in amount_matches:
                try:
                    amount = float(match.replace('$', '').replace(',', ''))
                    amounts.append(amount)
                except:
                    pass
            
            if amounts:
                # Assume largest amount is total
                total = max(amounts)
                fields.append(ExtractedField(
                    name="total_amount",
                    value=total,
                    confidence=0.8
                ))
                
                # Look for subtotal (usually before tax)
                if len(amounts) > 1:
                    subtotal = sorted(amounts)[-2] if len(amounts) > 1 else amounts[0]
                    fields.append(ExtractedField(
                        name="subtotal",
                        value=subtotal,
                        confidence=0.6
                    ))
        
        # Tax
        tax_pattern = r'(?:tax|vat|gst)[\s:]*\$?\s*(\d+(?:\.\d{2})?)'
        tax_match = re.search(tax_pattern, text, re.IGNORECASE)
        if tax_match:
            fields.append(ExtractedField(
                name="tax_amount",
                value=float(tax_match.group(1)),
                confidence=0.7
            ))
        
        # PO Number
        po_match = re.search(self.PATTERNS["po_number"], text, re.IGNORECASE)
        if po_match:
            fields.append(ExtractedField(
                name="po_number",
                value=po_match.group(1),
                confidence=0.8
            ))
        
        return fields
    
    async def _extract_receipt_fields(self, text: str) -> List[ExtractedField]:
        """Extract fields specific to receipts"""
        fields = []
        
        # Merchant name (usually at the top)
        lines = text.split('\n')
        if len(lines) > 0:
            for line in lines[:3]:
                if line.strip() and len(line.strip()) > 3:
                    fields.append(ExtractedField(
                        name="merchant_name",
                        value=line.strip(),
                        confidence=0.8
                    ))
                    break
        
        # Transaction date
        date_matches = re.findall(self.PATTERNS["date"], text)
        if date_matches:
            fields.append(ExtractedField(
                name="transaction_date",
                value=date_matches[0],
                confidence=0.9
            ))
        
        # Total amount
        total_pattern = r'(?:total|amount due|grand total)[\s:]*\$?\s*(\d+(?:\.\d{2})?)'
        total_match = re.search(total_pattern, text, re.IGNORECASE)
        if total_match:
            fields.append(ExtractedField(
                name="total_amount",
                value=float(total_match.group(1)),
                confidence=0.9
            ))
        
        # Payment method
        payment_patterns = [
            (r'(?:visa|mastercard|amex|discover)[\s\*]*(\d{4})', "credit_card"),
            (r'(?:cash)', "cash"),
            (r'(?:debit)', "debit_card"),
            (r'(?:check|cheque)', "check")
        ]
        
        for pattern, method in payment_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                fields.append(ExtractedField(
                    name="payment_method",
                    value=method,
                    confidence=0.8
                ))
                break
        
        # Receipt/Transaction number
        receipt_pattern = r'(?:receipt|transaction|trans)[\s#:]*([A-Z0-9\-]+)'
        receipt_match = re.search(receipt_pattern, text, re.IGNORECASE)
        if receipt_match:
            fields.append(ExtractedField(
                name="receipt_number",
                value=receipt_match.group(1),
                confidence=0.8
            ))
        
        return fields
    
    async def _extract_contract_fields(self, text: str) -> List[ExtractedField]:
        """Extract fields specific to contracts"""
        fields = []
        
        # Party names (look for "between" pattern)
        party_pattern = r'between\s+([^,\n]+?)\s+(?:and|,)\s+([^,\n]+)'
        party_match = re.search(party_pattern, text, re.IGNORECASE)
        if party_match:
            fields.append(ExtractedField(
                name="party1",
                value=party_match.group(1).strip(),
                confidence=0.8
            ))
            fields.append(ExtractedField(
                name="party2",
                value=party_match.group(2).strip(),
                confidence=0.8
            ))
        
        # Effective date
        effective_pattern = r'(?:effective|commencement|start).*?(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
        effective_match = re.search(effective_pattern, text, re.IGNORECASE)
        if effective_match:
            fields.append(ExtractedField(
                name="effective_date",
                value=effective_match.group(1),
                confidence=0.8
            ))
        
        # Termination/End date
        end_pattern = r'(?:termination|expiration|end).*?(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
        end_match = re.search(end_pattern, text, re.IGNORECASE)
        if end_match:
            fields.append(ExtractedField(
                name="end_date",
                value=end_match.group(1),
                confidence=0.7
            ))
        
        # Contract value/amount
        value_pattern = r'(?:total value|contract value|amount)[\s:]*\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)'
        value_match = re.search(value_pattern, text, re.IGNORECASE)
        if value_match:
            value = value_match.group(1).replace(',', '')
            fields.append(ExtractedField(
                name="contract_value",
                value=float(value),
                confidence=0.7
            ))
        
        return fields
    
    async def _extract_form_fields(self, text: str) -> List[ExtractedField]:
        """Extract fields from forms"""
        fields = []
        
        # Look for field:value patterns
        field_pattern = r'([A-Za-z\s]+?)[\s:]+([^\n]+)'
        field_matches = re.findall(field_pattern, text)
        
        for field_name, field_value in field_matches[:20]:  # Limit to 20 fields
            field_name = field_name.strip().lower().replace(' ', '_')
            field_value = field_value.strip()
            
            if field_name and field_value and len(field_name) < 50:
                fields.append(ExtractedField(
                    name=field_name,
                    value=field_value,
                    confidence=0.6
                ))
        
        # Extract email if present
        email_matches = re.findall(self.PATTERNS["email"], text)
        if email_matches:
            fields.append(ExtractedField(
                name="email",
                value=email_matches[0],
                confidence=0.9
            ))
        
        # Extract phone if present
        phone_matches = re.findall(self.PATTERNS["phone"], text)
        if phone_matches:
            fields.append(ExtractedField(
                name="phone",
                value=phone_matches[0],
                confidence=0.8
            ))
        
        return fields
    
    async def _extract_generic_fields(self, text: str) -> List[ExtractedField]:
        """Extract generic fields from any document"""
        fields = []
        
        # Extract all dates
        date_matches = re.findall(self.PATTERNS["date"], text)
        for i, date in enumerate(date_matches[:3]):  # Limit to 3 dates
            fields.append(ExtractedField(
                name=f"date_{i+1}",
                value=date,
                confidence=0.6
            ))
        
        # Extract all amounts
        amount_matches = re.findall(self.PATTERNS["amount"], text)
        for i, amount in enumerate(amount_matches[:5]):  # Limit to 5 amounts
            try:
                value = float(amount.replace('$', '').replace(',', ''))
                fields.append(ExtractedField(
                    name=f"amount_{i+1}",
                    value=value,
                    confidence=0.5
                ))
            except:
                pass
        
        # Extract email
        email_matches = re.findall(self.PATTERNS["email"], text)
        if email_matches:
            fields.append(ExtractedField(
                name="email",
                value=email_matches[0],
                confidence=0.9
            ))
        
        # Extract phone
        phone_matches = re.findall(self.PATTERNS["phone"], text)
        if phone_matches:
            fields.append(ExtractedField(
                name="phone",
                value=phone_matches[0],
                confidence=0.7
            ))
        
        return fields
    
    async def _extract_tables(self, text: str) -> List[ExtractedTable]:
        """Extract table data from text"""
        tables = []
        
        # Simple table detection - look for patterns with consistent delimiters
        lines = text.split('\n')
        potential_table_lines = []
        
        for line in lines:
            # Check if line has multiple columns (tab or multiple spaces)
            if '\t' in line or '  ' in line or '|' in line:
                potential_table_lines.append(line)
        
        # Group consecutive table lines
        if len(potential_table_lines) > 2:
            # Assume first line is header
            headers = re.split(r'\t+|\s{2,}|\|', potential_table_lines[0])
            headers = [h.strip() for h in headers if h.strip()]
            
            if len(headers) > 1:
                rows = []
                for line in potential_table_lines[1:]:
                    cells = re.split(r'\t+|\s{2,}|\|', line)
                    cells = [c.strip() for c in cells if c.strip()]
                    
                    if len(cells) == len(headers):
                        row = {headers[i]: cells[i] for i in range(len(headers))}
                        rows.append(row)
                
                if rows:
                    tables.append(ExtractedTable(
                        headers=headers,
                        rows=rows,
                        confidence=0.6
                    ))
        
        return tables