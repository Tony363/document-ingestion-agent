#!/usr/bin/env python3
"""
Test script for the Document Ingestion Agent v2.0
Tests the complete pipeline with a sample PDF/image
"""

import asyncio
import aiofiles
import httpx
import sys
import time
from pathlib import Path
import base64

# API Configuration
API_BASE_URL = "http://localhost:8000"

async def create_test_pdf():
    """Create a simple test PDF file"""
    try:
        # Use reportlab to create a simple PDF
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        pdf_path = "test_invoice.pdf"
        c = canvas.Canvas(pdf_path, pagesize=letter)
        
        # Add invoice content
        c.drawString(100, 750, "INVOICE")
        c.drawString(100, 700, "Invoice Number: INV-2025-001")
        c.drawString(100, 680, "Date: January 24, 2025")
        c.drawString(100, 650, "From: ABC Company")
        c.drawString(100, 630, "123 Business St, City, State 12345")
        c.drawString(100, 600, "To: XYZ Customer")
        c.drawString(100, 580, "456 Client Ave, Town, State 67890")
        c.drawString(100, 550, "Description: Professional Services")
        c.drawString(100, 530, "Amount: $1,500.00")
        c.drawString(100, 500, "Tax (10%): $150.00")
        c.drawString(100, 480, "Total Due: $1,650.00")
        c.drawString(100, 450, "Payment Terms: Net 30")
        
        c.save()
        print(f"✅ Created test PDF: {pdf_path}")
        return pdf_path
    except ImportError:
        print("⚠️ reportlab not installed, creating a simple text file instead")
        # Create a simple text file as fallback
        text_path = "test_invoice.txt"
        with open(text_path, 'w') as f:
            f.write("INVOICE\n")
            f.write("Invoice Number: INV-2025-001\n")
            f.write("Date: January 24, 2025\n")
            f.write("From: ABC Company\n")
            f.write("To: XYZ Customer\n")
            f.write("Total Due: $1,650.00\n")
        return text_path

async def test_health_check():
    """Test the health check endpoint"""
    print("\n🔍 Testing health check...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed")
            print(f"   Status: {data['status']}")
            print(f"   Version: {data['version']}")
            print(f"   Agents: {', '.join(data['agents_status'].keys())}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False

async def test_document_upload(file_path: str):
    """Test document upload and processing"""
    print(f"\n📤 Uploading document: {file_path}")
    
    # Read file content
    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        print(f"❌ File not found: {file_path}")
        return None
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Prepare file upload
        with open(file_path, 'rb') as f:
            files = {'file': (file_path_obj.name, f, 'application/pdf')}
            data = {'document_type': 'invoice'}
            
            # Upload document
            response = await client.post(
                f"{API_BASE_URL}/documents/upload",
                files=files,
                data=data
            )
        
        if response.status_code == 200:
            data = response.json()
            document_id = data['document_id']
            print(f"✅ Document uploaded successfully")
            print(f"   Document ID: {document_id}")
            print(f"   Status: {data['status']}")
            print(f"   Message: {data['message']}")
            return document_id
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None

async def monitor_processing(document_id: str, max_wait: int = 60):
    """Monitor document processing status"""
    print(f"\n⏳ Monitoring processing for document: {document_id}")
    
    start_time = time.time()
    last_status = None
    last_stage = None
    
    async with httpx.AsyncClient() as client:
        while time.time() - start_time < max_wait:
            response = await client.get(f"{API_BASE_URL}/documents/{document_id}/status")
            
            if response.status_code == 200:
                data = response.json()
                status = data['status']
                stage = data['processing_stage']
                progress = data['progress']
                
                # Print updates only when status or stage changes
                if status != last_status or stage != last_stage:
                    print(f"   [{int(progress*100)}%] Stage: {stage} | Status: {status}")
                    last_status = status
                    last_stage = stage
                
                # Check if processing is complete
                if status in ['completed', 'webhook_ready', 'failed']:
                    if status == 'failed':
                        print(f"❌ Processing failed: {data.get('error_message', 'Unknown error')}")
                        return False
                    else:
                        print(f"✅ Processing completed successfully")
                        print(f"   Final status: {status}")
                        print(f"   Processing time: {time.time() - start_time:.2f} seconds")
                        return True
            else:
                print(f"⚠️ Failed to get status: {response.status_code}")
            
            # Wait before next check
            await asyncio.sleep(2)
        
        print(f"⏱️ Timeout: Processing did not complete within {max_wait} seconds")
        return False

async def test_get_content(document_id: str):
    """Test retrieving extracted content"""
    print(f"\n📋 Retrieving extracted content...")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/documents/{document_id}/content")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Content retrieved successfully")
            print(f"   Document Type: {data['document_type']}")
            print(f"   Confidence Score: {data['confidence_score']:.2%}")
            print(f"   Extracted Fields:")
            for field, value in data['structured_content'].items():
                print(f"      - {field}: {value}")
            print(f"   Processing Time: {data['metadata'].get('processing_time', 0):.2f}s")
            return True
        else:
            print(f"❌ Failed to retrieve content: {response.status_code}")
            print(f"   Error: {response.text}")
            return False

async def test_get_schema(document_id: str):
    """Test retrieving generated JSON schema"""
    print(f"\n📐 Retrieving JSON schema...")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/documents/{document_id}/schema")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Schema retrieved successfully")
            print(f"   Document Type: {data['document_type']}")
            print(f"   Schema Version: {data['schema_version']}")
            print(f"   Webhook Ready: {data['webhook_ready']}")
            print(f"   Extraction Confidence: {data['extraction_confidence']:.2%}")
            
            # Pretty print schema structure
            import json
            print(f"   Schema Structure:")
            schema_str = json.dumps(data['schema'], indent=6)
            for line in schema_str.split('\n'):
                print(f"      {line}")
            
            return True
        else:
            print(f"❌ Failed to retrieve schema: {response.status_code}")
            print(f"   Error: {response.text}")
            return False

async def main():
    """Main test execution"""
    print("=" * 60)
    print("Document Ingestion Agent v2.0 - Pipeline Test")
    print("=" * 60)
    
    # Check if server is running
    try:
        # Test health check
        if not await test_health_check():
            print("\n❌ Server is not responding. Please start the server first:")
            print("   python -m uvicorn app.main:app --reload")
            return
        
        # Create test document
        test_file = await create_test_pdf()
        
        # Upload and process document
        document_id = await test_document_upload(test_file)
        if not document_id:
            print("\n❌ Document upload failed. Cannot continue tests.")
            return
        
        # Monitor processing
        if not await monitor_processing(document_id):
            print("\n❌ Document processing failed. Cannot retrieve results.")
            return
        
        # Retrieve and display results
        await test_get_content(document_id)
        await test_get_schema(document_id)
        
        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        print("=" * 60)
        
        # Clean up test file
        Path(test_file).unlink(missing_ok=True)
        print(f"\n🧹 Cleaned up test file: {test_file}")
        
    except httpx.ConnectError:
        print("\n❌ Cannot connect to server. Please ensure the server is running:")
        print("   python -m uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())