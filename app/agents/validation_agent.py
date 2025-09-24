"""
Validation Agent

Validates extracted data and schemas against business rules
and data quality requirements.
"""

from typing import Dict, Any, List, Optional
import jsonschema
from pydantic import BaseModel, Field
import re

from .base_agent import BaseAgent, AgentContext
from .schema_generation_agent import DocumentSchema

class ValidationRule(BaseModel):
    """Validation rule definition"""
    field: str
    rule_type: str  # "required", "format", "range", "regex", "custom"
    parameters: Dict[str, Any] = Field(default_factory=dict)
    error_message: str
    severity: str = "error"  # "error", "warning", "info"

class ValidationInput(BaseModel):
    """Input for validation"""
    schema: Dict[str, Any]
    document_type: str
    strict_mode: bool = True

class ValidationResult(BaseModel):
    """Single validation result"""
    field: str
    rule: str
    passed: bool
    message: str
    severity: str
    value: Optional[Any] = None

class ValidationOutput(BaseModel):
    """Output from validation"""
    is_valid: bool
    validation_score: float
    total_checks: int
    passed_checks: int
    failed_checks: int
    results: List[ValidationResult]
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]

class ValidationAgent(BaseAgent[ValidationInput, ValidationOutput]):
    """
    Agent for validating extracted data and schemas
    """
    
    # Validation rules per document type
    VALIDATION_RULES = {
        "invoice": [
            ValidationRule(
                field="invoice_number",
                rule_type="required",
                parameters={},
                error_message="Invoice number is required"
            ),
            ValidationRule(
                field="vendor_name",
                rule_type="required",
                parameters={},
                error_message="Vendor name is required"
            ),
            ValidationRule(
                field="total_amount",
                rule_type="required",
                parameters={},
                error_message="Total amount is required"
            ),
            ValidationRule(
                field="total_amount",
                rule_type="range",
                parameters={"min": 0, "max": 1000000},
                error_message="Total amount must be between 0 and 1,000,000"
            ),
            ValidationRule(
                field="invoice_date",
                rule_type="format",
                parameters={"format": "date"},
                error_message="Invoice date must be a valid date",
                severity="warning"
            )
        ],
        "receipt": [
            ValidationRule(
                field="merchant_name",
                rule_type="required",
                parameters={},
                error_message="Merchant name is required"
            ),
            ValidationRule(
                field="total_amount",
                rule_type="required",
                parameters={},
                error_message="Total amount is required"
            ),
            ValidationRule(
                field="transaction_date",
                rule_type="required",
                parameters={},
                error_message="Transaction date is required"
            )
        ],
        "contract": [
            ValidationRule(
                field="party1",
                rule_type="required",
                parameters={},
                error_message="First party name is required"
            ),
            ValidationRule(
                field="party2",
                rule_type="required",
                parameters={},
                error_message="Second party name is required"
            ),
            ValidationRule(
                field="effective_date",
                rule_type="required",
                parameters={},
                error_message="Effective date is required"
            )
        ],
        "form": [
            ValidationRule(
                field="email",
                rule_type="format",
                parameters={"format": "email"},
                error_message="Email must be valid format",
                severity="warning"
            ),
            ValidationRule(
                field="phone",
                rule_type="format",
                parameters={"format": "phone"},
                error_message="Phone must be valid format",
                severity="warning"
            )
        ]
    }
    
    # Format validators
    FORMAT_VALIDATORS = {
        "email": r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        "phone": r'^\+?1?\d{9,15}$',
        "date": r'^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$|\d{4}[-/]\d{1,2}[-/]\d{1,2}$',
        "zipcode": r'^\d{5}(-\d{4})?$',
        "ssn": r'^\d{3}-?\d{2}-?\d{4}$'
    }
    
    def __init__(self):
        super().__init__(
            name="validation_agent",
            max_retries=2,
            timeout=15.0
        )
        
    async def validate_input(self, input_data: ValidationInput) -> bool:
        """Validate validation input"""
        if not input_data.schema:
            return False
        if not input_data.document_type:
            return False
        return True
    
    async def process(
        self,
        input_data: ValidationInput,
        context: AgentContext
    ) -> ValidationOutput:
        """
        Validate document schema against rules
        
        Args:
            input_data: Validation input with schema and rules
            context: Agent execution context
            
        Returns:
            Validation output with results
        """
        results = []
        errors = []
        warnings = []
        suggestions = []
        
        # Get validation rules for document type
        rules = self.VALIDATION_RULES.get(input_data.document_type, [])
        
        # Add generic validation rules
        rules.extend(await self._get_generic_rules())
        
        # Extract data from schema
        schema_data = input_data.schema
        extracted_data = schema_data.get("extracted_data", {})
        fields = extracted_data.get("fields", {})
        structured = extracted_data.get("structured", {})
        
        # Flatten structured data for validation
        flat_data = await self._flatten_data(structured, fields)
        
        # Apply validation rules
        for rule in rules:
            result = await self._apply_rule(rule, flat_data, input_data.strict_mode)
            results.append(result)
            
            if not result.passed:
                if result.severity == "error":
                    errors.append(result.message)
                elif result.severity == "warning":
                    warnings.append(result.message)
        
        # Schema structure validation
        structure_results = await self._validate_schema_structure(schema_data)
        results.extend(structure_results)
        
        # Cross-field validation
        cross_field_results = await self._validate_cross_fields(
            flat_data,
            input_data.document_type
        )
        results.extend(cross_field_results)
        
        # Data quality checks
        quality_results = await self._validate_data_quality(flat_data)
        results.extend(quality_results)
        
        # Generate suggestions
        suggestions = await self._generate_suggestions(
            results,
            flat_data,
            input_data.document_type
        )
        
        # Calculate validation score
        passed_checks = sum(1 for r in results if r.passed)
        total_checks = len(results)
        validation_score = passed_checks / total_checks if total_checks > 0 else 0.0
        
        # Determine overall validity
        critical_errors = [r for r in results if not r.passed and r.severity == "error"]
        is_valid = len(critical_errors) == 0 if input_data.strict_mode else validation_score >= 0.7
        
        return ValidationOutput(
            is_valid=is_valid,
            validation_score=validation_score,
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=total_checks - passed_checks,
            results=results,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    async def _flatten_data(
        self,
        structured: Dict[str, Any],
        fields: Dict[str, Any],
        prefix: str = ""
    ) -> Dict[str, Any]:
        """
        Flatten nested data structure for validation
        
        Args:
            structured: Structured data
            fields: Field data
            prefix: Key prefix for nested fields
            
        Returns:
            Flattened data dictionary
        """
        flat = {}
        
        # Add fields
        for key, value in fields.items():
            if isinstance(value, dict) and "value" in value:
                flat[key] = value["value"]
            else:
                flat[key] = value
        
        # Recursively flatten structured data
        def flatten_dict(d, parent_key=""):
            for k, v in d.items():
                new_key = f"{parent_key}.{k}" if parent_key else k
                
                if isinstance(v, dict) and not any(isinstance(vv, (list, dict)) for vv in v.values()):
                    for sub_k, sub_v in v.items():
                        flat[f"{new_key}.{sub_k}" if new_key else sub_k] = sub_v
                elif not isinstance(v, (dict, list)):
                    flat[new_key] = v
        
        if structured:
            flatten_dict(structured, prefix)
        
        return flat
    
    async def _apply_rule(
        self,
        rule: ValidationRule,
        data: Dict[str, Any],
        strict_mode: bool
    ) -> ValidationResult:
        """
        Apply a single validation rule
        
        Args:
            rule: Validation rule to apply
            data: Data to validate
            strict_mode: Whether to use strict validation
            
        Returns:
            Validation result
        """
        field_value = None
        
        # Try to find field in data (check multiple possible keys)
        possible_keys = [
            rule.field,
            rule.field.replace("_", "."),
            f"fields.{rule.field}",
            f"structured.{rule.field}"
        ]
        
        for key in possible_keys:
            if key in data:
                field_value = data[key]
                break
            # Check nested keys
            parts = key.split(".")
            if len(parts) > 1:
                for k, v in data.items():
                    if k.endswith(parts[-1]):
                        field_value = v
                        break
        
        passed = True
        message = ""
        
        if rule.rule_type == "required":
            passed = field_value is not None and field_value != ""
            if not passed:
                message = rule.error_message
        
        elif rule.rule_type == "format":
            if field_value:
                format_type = rule.parameters.get("format")
                pattern = self.FORMAT_VALIDATORS.get(format_type)
                if pattern:
                    passed = bool(re.match(pattern, str(field_value)))
                    if not passed:
                        message = rule.error_message
        
        elif rule.rule_type == "range":
            if field_value is not None:
                try:
                    value = float(field_value)
                    min_val = rule.parameters.get("min")
                    max_val = rule.parameters.get("max")
                    
                    if min_val is not None and value < min_val:
                        passed = False
                        message = f"Value {value} is below minimum {min_val}"
                    elif max_val is not None and value > max_val:
                        passed = False
                        message = f"Value {value} exceeds maximum {max_val}"
                except:
                    passed = False
                    message = "Value is not numeric"
        
        elif rule.rule_type == "regex":
            if field_value:
                pattern = rule.parameters.get("pattern")
                if pattern:
                    passed = bool(re.match(pattern, str(field_value)))
                    if not passed:
                        message = rule.error_message
        
        return ValidationResult(
            field=rule.field,
            rule=rule.rule_type,
            passed=passed,
            message=message or "Validation passed",
            severity=rule.severity if not passed else "info",
            value=field_value
        )
    
    async def _validate_schema_structure(
        self,
        schema_data: Dict[str, Any]
    ) -> List[ValidationResult]:
        """
        Validate schema structure
        
        Args:
            schema_data: Schema to validate
            
        Returns:
            List of validation results
        """
        results = []
        
        # Check required schema fields
        required_fields = ["schema_version", "document_id", "document_type", "extracted_data"]
        
        for field in required_fields:
            if field in schema_data:
                results.append(ValidationResult(
                    field=f"schema.{field}",
                    rule="structure",
                    passed=True,
                    message=f"Schema field {field} is present",
                    severity="info"
                ))
            else:
                results.append(ValidationResult(
                    field=f"schema.{field}",
                    rule="structure",
                    passed=False,
                    message=f"Schema field {field} is missing",
                    severity="error"
                ))
        
        return results
    
    async def _validate_cross_fields(
        self,
        data: Dict[str, Any],
        document_type: str
    ) -> List[ValidationResult]:
        """
        Validate relationships between fields
        
        Args:
            data: Data to validate
            document_type: Type of document
            
        Returns:
            List of validation results
        """
        results = []
        
        if document_type == "invoice":
            # Check if total = subtotal + tax
            subtotal = data.get("subtotal") or data.get("amounts.subtotal")
            tax = data.get("tax_amount") or data.get("amounts.tax")
            total = data.get("total_amount") or data.get("amounts.total")
            
            if subtotal and tax and total:
                try:
                    calculated = float(subtotal) + float(tax)
                    actual = float(total)
                    
                    if abs(calculated - actual) < 0.01:
                        results.append(ValidationResult(
                            field="total_amount",
                            rule="cross_field",
                            passed=True,
                            message="Total amount matches subtotal + tax",
                            severity="info"
                        ))
                    else:
                        results.append(ValidationResult(
                            field="total_amount",
                            rule="cross_field",
                            passed=False,
                            message=f"Total {actual} doesn't match subtotal {subtotal} + tax {tax}",
                            severity="warning"
                        ))
                except:
                    pass
        
        return results
    
    async def _validate_data_quality(
        self,
        data: Dict[str, Any]
    ) -> List[ValidationResult]:
        """
        Validate data quality metrics
        
        Args:
            data: Data to validate
            
        Returns:
            List of validation results
        """
        results = []
        
        # Check for completeness
        non_empty_fields = sum(1 for v in data.values() if v)
        total_fields = len(data)
        
        completeness = non_empty_fields / total_fields if total_fields > 0 else 0
        
        if completeness >= 0.7:
            results.append(ValidationResult(
                field="data_completeness",
                rule="quality",
                passed=True,
                message=f"Data is {completeness*100:.1f}% complete",
                severity="info"
            ))
        else:
            results.append(ValidationResult(
                field="data_completeness",
                rule="quality",
                passed=False,
                message=f"Data is only {completeness*100:.1f}% complete",
                severity="warning"
            ))
        
        return results
    
    async def _get_generic_rules(self) -> List[ValidationRule]:
        """Get generic validation rules applicable to all documents"""
        return [
            ValidationRule(
                field="confidence_score",
                rule_type="range",
                parameters={"min": 0.5, "max": 1.0},
                error_message="Confidence score should be between 0.5 and 1.0",
                severity="warning"
            )
        ]
    
    async def _generate_suggestions(
        self,
        results: List[ValidationResult],
        data: Dict[str, Any],
        document_type: str
    ) -> List[str]:
        """
        Generate improvement suggestions based on validation results
        
        Args:
            results: Validation results
            data: Validated data
            document_type: Type of document
            
        Returns:
            List of suggestions
        """
        suggestions = []
        
        # Check for missing required fields
        failed_required = [r for r in results if r.rule == "required" and not r.passed]
        if failed_required:
            fields = ", ".join([r.field for r in failed_required])
            suggestions.append(f"Consider manual review to fill missing fields: {fields}")
        
        # Check for format issues
        failed_format = [r for r in results if r.rule == "format" and not r.passed]
        if failed_format:
            suggestions.append("Review and correct format issues in extracted data")
        
        # Document-specific suggestions
        if document_type == "invoice" and not data.get("line_items"):
            suggestions.append("Consider extracting line items for detailed invoice analysis")
        
        if document_type == "contract" and not data.get("terms"):
            suggestions.append("Contract terms extraction could improve automation accuracy")
        
        return suggestions