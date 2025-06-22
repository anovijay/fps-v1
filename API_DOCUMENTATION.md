# LLM Adapter Service - API Documentation

## Overview

The **LLM Adapter Service** is an intelligent email and document processing API that extracts structured data from emails and their attachments using OpenAI's GPT models. The service specializes in financial document processing with smart payment status detection and calendar event generation.

### Base Information
- **Service Name**: LLM Adapter Service
- **Version**: 1.0.0
- **Base URL**: `https://your-llm-adapter-service.run.app`
- **Content-Type**: `application/json`

## Key Features

### 🤖 **Intelligent Document Processing**
- Supports PDF, DOCX, TXT, and other document formats
- Native OpenAI file processing with local fallback
- Smart payment status detection (Paid/Unpaid/Unknown)
- Multilingual support (English/German payment terms)

### 📅 **Calendar Integration**
- Automatic calendar event generation for due dates
- Structured execution details for automation
- Source traceability (email → file → calendar event)

### ⚡ **Flexible Input Formats**
- Legacy payload format support
- New structured format with GCS integration
- Backward compatibility maintained

---

## API Endpoints

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "llm-adapter", 
  "version": "1.0.0",
  "openai_configured": true
}
```

### Data Extraction
```http
POST /extract
```

---

## Request Schema

The service accepts **two payload formats** for maximum flexibility:

### Format 1: New Structure (Recommended)

**Use this format when:**
- Files are stored in Google Cloud Storage
- You need structured email metadata
- Working with newer integrations

```json
{
  "extraction_timestamp": "2025-01-15T12:00:00.000000",
  "total_emails": 2,
  "emails": [
    {
      "id": "email_001",
      "subject": "Invoice #INV-2025-001",
      "sender_email_id": "billing@company.com",
      "body": "Dear Customer, please find your invoice attached.",
      "has_attachments": true,
      "updated_at": "2025-01-15T12:00:00.000000",
      "files": [
        {
          "id": "file_001", 
          "file_name": "invoice_2025_001.pdf",
          "cloud_storage_url": "gs://your-bucket/invoices/invoice_2025_001.pdf"
        }
      ]
    }
  ]
}
```

**Required Fields:**
- `emails` (array): List of email objects
- `emails[].id` (string): Unique email identifier
- `files[].id` (string): Unique file identifier  
- `files[].file_name` (string): Original filename
- `files[].cloud_storage_url` (string): GCS URL (must start with `gs://`)

**Optional Fields:**
- `extraction_timestamp`: When emails were extracted
- `total_emails`: Total count for validation
- `subject`, `sender_email_id`, `body`: Email content
- `has_attachments`, `updated_at`: Metadata

### Format 2: Legacy Structure

**Use this format when:**
- Migrating from older systems
- Files are already text-extracted
- Simple integration requirements

```json
{
  "mails": {
    "mail_001": {
      "meta": {
        "subject": "Invoice #INV-2025-001",
        "from": "billing@company.com", 
        "date": "2025-01-15T12:00:00Z"
      },
      "body": "Dear Customer, please find your invoice attached.",
      "attachments": {
        "att_001": {
          "content": "INVOICE\nCompany XYZ\nAmount: €1,200.00\nDue: 2025-01-30",
          "filename": "invoice_2025_001.pdf",
          "gcs_url": "gs://your-bucket/invoices/invoice_2025_001.pdf"
        }
      }
    }
  }
}
```

**Required Fields:**
- `mails` (object): Mapping of mail IDs to mail data
- `mails[mail_id]` (object): Email data object

**Optional Fields:**
- `meta`: Email metadata (subject, from, date)
- `body`: Email body content
- `attachments`: File attachments with content or GCS URLs

---

## Response Schema

The service returns structured data with intelligent extraction results:

```json
{
  "status": "success",
  "results": {
    "email_001": {
      "Summary": "Invoice from Company XYZ for consulting services. Payment due by 2025-01-30.",
      "ActionItems": [
        "Make payment by 2025-01-30",
        "Review consulting deliverables"
      ],
      "Urgency": "High",
      "files": {
        "file_001": {
          "Type": "Invoice",
          "sender": "Company XYZ",
          "received_date": "2025-01-15",
          "Summary": "Consulting services invoice for December 2024",
          "Details": "Professional consulting services provided during December 2024. Total amount €1,200.00 due by January 30, 2025.",
          "tags": ["Invoice", "Consulting", "Payment Due"],
          "Urgency": "High",
          "Status": "Unpaid",
          "ActionRequired": "Make payment by due date",
          "Amount": "€1,200.00",
          "PaymentDetails": {
            "due_date": "2025-01-30",
            "method": "Bank transfer",
            "reference": "INV-2025-001"
          }
        }
      },
      "calendar_add_details": [
        {
          "date": "2025-01-30",
          "time": "09:00", 
          "action": "Pay Company XYZ invoice",
          "source_mail_id": "email_001",
          "source_file_id": "file_001",
          "execution_details": {
            "amount": "€1,200.00",
            "reference": "INV-2025-001",
            "recipient": "Company XYZ"
          }
        }
      ]
    }
  }
}
```

### Response Field Definitions

#### Per Email Object
| Field | Type | Description |
|-------|------|-------------|
| `Summary` | string | Human-readable summary of email and purpose |
| `ActionItems` | array[string] | List of actionable tasks for the user |
| `Urgency` | enum | `Low` \| `Medium` \| `High` \| `Critical` |
| `files` | object | Details about processed attachments (optional) |
| `calendar_add_details` | array | Calendar events to create |

#### Per File Object (within `files`)
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `Type` | string | ✅ | Document type (Invoice, Receipt, etc.) |
| `sender` | string | ✅ | Document sender/issuer |
| `received_date` | string | ✅ | Document date |
| `Summary` | string | ✅ | Brief document summary |
| `Details` | string | ✅ | Detailed document information |
| `tags` | array[string] | ✅ | Relevant document tags |
| `Urgency` | enum | ✅ | `Low` \| `Medium` \| `High` \| `Critical` |
| `Status` | enum | ⚪ | `Paid` \| `Unpaid` \| `Unknown` |
| `ActionRequired` | string | ⚪ | Required action description |
| `Amount` | string | ⚪ | Monetary amount if applicable |
| `PaymentDetails` | object | ⚪ | Payment information structure |

*Additional fields may be added dynamically based on document content (e.g., `Authority`, `Reference`, `Location`)*

#### Calendar Event Object
| Field | Type | Description |
|-------|------|-------------|
| `date` | string | Event date (YYYY-MM-DD) |
| `time` | string | Event time (HH:mm) |
| `action` | string | Human-readable action description |
| `source_mail_id` | string | Source email ID |
| `source_file_id` | string | Source file ID (or `null`) |
| `execution_details` | object | Structured data for automation |

---

## Payment Intelligence

### Smart Payment Detection
The service automatically detects payment status using multiple indicators:

**Detection Keywords:**
- English: "Paid", "Payment Received", "Transaction Complete"
- German: "Zahlung", "SEPA-Lastschrift", "Bezahlt"

**Payment Status Logic:**
```json
// ✅ PAID DOCUMENT
{
  "ActionItems": ["No action required. Payment already completed."],
  "files": {
    "file_id": {
      "Status": "Paid"
    }
  },
  "calendar_add_details": []  // No calendar events needed
}

// ❌ UNPAID DOCUMENT  
{
  "ActionItems": ["Make payment by 2025-01-30"],
  "files": {
    "file_id": {
      "Status": "Unpaid"
    }
  },
  "calendar_add_details": [
    {
      "action": "Pay invoice",
      "execution_details": {
        "amount": "€1,200.00"
      }
    }
  ]
}
```

---

## Error Handling

### HTTP Status Codes
| Code | Description | Example Response |
|------|-------------|------------------|
| 200 | Success | See response schema above |
| 400 | Bad Request | `{"detail": "No emails found in payload"}` |
| 500 | Server Error | `{"detail": "OpenAI API connection failed"}` |

### Common Error Scenarios
```json
// Invalid payload structure
{
  "detail": "No emails found in payload"
}

// GCS access issues
{
  "detail": "Failed to download file from GCS: gs://bucket/file.pdf"
}

// OpenAI API issues  
{
  "detail": "OpenAI client not configured"
}
```

---

## Integration Examples

### Example 1: Node.js Integration
```javascript
const extractData = async (emailData) => {
  const response = await fetch('https://your-service.run.app/extract', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      extraction_timestamp: new Date().toISOString(),
      total_emails: emailData.length,
      emails: emailData
    })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }
  
  return await response.json();
};
```

### Example 2: Python Integration
```python
import requests
from datetime import datetime

def extract_email_data(emails):
    url = "https://your-service.run.app/extract"
    payload = {
        "extraction_timestamp": datetime.now().isoformat(),
        "total_emails": len(emails),
        "emails": emails
    }
    
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()
```

### Example 3: cURL Command
```bash
curl -X POST "https://your-service.run.app/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "emails": [
      {
        "id": "test_email_001",
        "subject": "Test Invoice",
        "body": "Please find attached invoice.",
        "files": [
          {
            "id": "test_file_001",
            "file_name": "invoice.pdf", 
            "cloud_storage_url": "gs://your-bucket/invoice.pdf"
          }
        ]
      }
    ]
  }'
```

---

## Best Practices

### 1. **File Storage**
- Store files in Google Cloud Storage with public read access
- Use consistent bucket naming and file organization
- Include file extensions for proper type detection

### 2. **Email IDs**
- Use unique, persistent identifiers for emails
- Avoid sequential numbering in production
- Include timestamp or hash for uniqueness

### 3. **Error Handling**
- Always check HTTP status codes
- Parse error messages for debugging
- Implement retry logic for 500 errors

### 4. **Performance**
- Batch multiple emails in single request when possible
- Monitor response times for large attachments
- Consider async processing for high volumes

### 5. **Calendar Integration**
- Use `calendar_add_details` for automated calendar creation
- Map `execution_details` to your calendar system fields
- Respect user time zones in calendar events

---

## Testing

### Health Check Test
```bash
curl https://your-service.run.app/health
```

Expected Response:
```json
{
  "status": "healthy",
  "service": "llm-adapter",
  "version": "1.0.0", 
  "openai_configured": true
}
```

### Sample Test Data
Use the test endpoint with sample GCS data:
```bash
curl https://your-service.run.app/test-gcs-data
```

---

## Support & Contact

For technical support or questions about integration:

- **Documentation**: This document
- **API Specification**: See `openAPI.yaml` for detailed schema
- **Health Monitoring**: Use `/health` endpoint for service status

---

*Last Updated: January 2025*
*API Version: 1.0.0* 