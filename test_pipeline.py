#!/usr/bin/env python3
"""
Test Script for Document Ingestion Pipeline

Demonstrates the complete document processing flow.
"""

import asyncio
import httpx
import sys
from pathlib import Path
import json
import time

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
API_KEY = "test-api-key"  # Replace with actual API key if enabled

async def test_document_upload(file_path: str):
    """Test document upload and processing"""
    
    print(f"\n{'='*60}")
    print("Document Ingestion Agent - Test Pipeline")
    print(f"{'='*60}\n")
    
    async with httpx.AsyncClient() as client:
        # 1. Upload Document
        print(f"1. Uploading document: {file_path}")
        
        with open(file_path, "rb") as f:
            files = {"file": (Path(file_path).name, f, "application/pdf")}
            headers = {"X-API-Key": API_KEY} if API_KEY else {}
            
            response = await client.post(
                f"{API_BASE_URL}/documents/upload",
                files=files,
                headers=headers
            )
        
        if response.status_code != 202:
            print(f"Error uploading document: {response.text}")
            return
        
        upload_result = response.json()
        job_id = upload_result["job_id"]
        document_id = upload_result["document_id"]
        
        print(f"   ✓ Document uploaded successfully")
        print(f"   - Job ID: {job_id}")
        print(f"   - Document ID: {document_id}")
        
        # 2. Check Processing Status
        print(f"\n2. Checking processing status...")
        
        max_attempts = 30  # Wait up to 30 seconds
        for attempt in range(max_attempts):
            response = await client.get(
                f"{API_BASE_URL}/documents/{document_id}/status",
                headers=headers
            )
            
            if response.status_code != 200:
                print(f"Error checking status: {response.text}")
                return
            
            status = response.json()
            
            if status["status"] == "completed":
                print(f"   ✓ Document processing completed")
                break
            elif status["status"] == "failed":
                print(f"   ✗ Document processing failed: {status.get('error', 'Unknown error')}")
                return
            else:
                print(f"   ... Processing (Stage: {status.get('pipeline_state', {}).get('stage', 'unknown')})")
                await asyncio.sleep(1)
        else:
            print("   ⚠ Processing timeout - still in progress")
            return
        
        # 3. Retrieve Generated Schema
        print(f"\n3. Retrieving generated JSON schema...")
        
        response = await client.get(
            f"{API_BASE_URL}/documents/{document_id}/schema",
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"Error retrieving schema: {response.text}")
            return
        
        schema = response.json()
        print(f"   ✓ Schema retrieved successfully")
        
        # 4. Display Results
        print(f"\n4. Document Processing Results:")
        print(f"   {'='*50}")
        
        print(f"   Document Type: {schema.get('document_type', 'Unknown')}")
        print(f"   Confidence Score: {schema.get('confidence_score', 0):.2%}")
        print(f"   Validation Status: {schema.get('validation_status', 'Unknown')}")
        
        # Display extracted fields
        extracted_data = schema.get("extracted_data", {})
        fields = extracted_data.get("fields", {})
        
        if fields:
            print(f"\n   Extracted Fields:")
            for field_name, field_data in fields.items():
                if isinstance(field_data, dict):
                    value = field_data.get("value", "N/A")
                    confidence = field_data.get("confidence", 0)
                    print(f"   - {field_name}: {value} (confidence: {confidence:.2%})")
                else:
                    print(f"   - {field_name}: {field_data}")
        
        # Display automation triggers
        triggers = schema.get("automation_triggers", [])
        if triggers:
            print(f"\n   Automation Triggers:")
            for trigger in triggers:
                print(f"   - Action: {trigger.get('action', 'Unknown')}")
                print(f"     Endpoint: {trigger.get('endpoint', 'N/A')}")
                if trigger.get("condition"):
                    print(f"     Condition: {json.dumps(trigger['condition'], indent=6)}")
        
        # Save schema to file
        output_file = f"output_schema_{document_id}.json"
        with open(output_file, "w") as f:
            json.dump(schema, f, indent=2)
        print(f"\n   ✓ Full schema saved to: {output_file}")
        
        print(f"\n{'='*60}")
        print("Test completed successfully!")
        print(f"{'='*60}\n")

async def test_webhook_registration():
    """Test webhook registration"""
    print("\n5. Testing Webhook Registration...")
    
    async with httpx.AsyncClient() as client:
        headers = {"X-API-Key": API_KEY} if API_KEY else {}
        
        # Register a webhook
        webhook_data = {
            "webhook_url": "https://example.com/webhook",
            "webhook_name": "Test Webhook",
            "events": ["document.processed", "document.validated"]
        }
        
        response = await client.post(
            f"{API_BASE_URL}/webhooks/register",
            params=webhook_data,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✓ Webhook registered: {result['webhook_id']}")
            
            # List webhooks
            response = await client.get(
                f"{API_BASE_URL}/webhooks/list",
                headers=headers
            )
            
            if response.status_code == 200:
                webhooks = response.json()
                print(f"   ✓ Total registered webhooks: {webhooks['total']}")

def create_sample_document():
    """Create a sample document for testing"""
    sample_content = """
    INVOICE
    
    Invoice Number: INV-2024-001
    Date: 01/15/2024
    
    Bill To:
    Acme Corporation
    123 Business Street
    New York, NY 10001
    
    Description             Quantity    Price       Total
    Product A               10          $50.00      $500.00
    Service B               5           $100.00     $500.00
    
    Subtotal:                                       $1000.00
    Tax (10%):                                      $100.00
    Total Amount Due:                               $1100.00
    
    Due Date: 02/15/2024
    """
    
    # Create a simple text file as PDF is not easily generated
    sample_file = "sample_invoice.txt"
    with open(sample_file, "w") as f:
        f.write(sample_content)
    
    print(f"Created sample document: {sample_file}")
    return sample_file

async def main():
    """Main test function"""
    
    # Check if a file path was provided
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        # Create a sample document for testing
        file_path = create_sample_document()
    
    # Verify file exists
    if not Path(file_path).exists():
        print(f"Error: File not found: {file_path}")
        return
    
    # Run tests
    await test_document_upload(file_path)
    await test_webhook_registration()

if __name__ == "__main__":
    print("Starting Document Ingestion Agent Test...")
    print("Make sure the API server is running on http://localhost:8000")
    print("-" * 60)
    
    asyncio.run(main())