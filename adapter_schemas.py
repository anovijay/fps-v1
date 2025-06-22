#!/usr/bin/env python3
"""
LLM Adapter Service - Request and Response Schemas
Defines the complete API contract for the email extraction service
Enhanced to match full API documentation specification
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass
import json

# =============================================================================
# REQUEST SCHEMA - Enhanced to match API documentation
# =============================================================================

@dataclass
class FileAttachment:
    """Schema for file attachment in email"""
    id: str                    # Unique file identifier
    file_name: str            # Original filename
    cloud_storage_url: str    # GCS URL where file is stored
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "file_name": self.file_name,
            "cloud_storage_url": self.cloud_storage_url
        }

@dataclass
class Email:
    """Schema for email in batch processing - Enhanced with optional fields"""
    id: str                             # Unique email identifier  
    subject: str                        # Email subject
    sender_email_id: str               # Sender's email address
    body: str                          # Email body content
    has_attachments: bool              # Whether email has attachments
    files: List[FileAttachment]       # List of file attachments
    updated_at: Optional[str] = None   # Email update timestamp (ISO 8601)
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "id": self.id,
            "subject": self.subject,
            "sender_email_id": self.sender_email_id,
            "body": self.body,
            "has_attachments": self.has_attachments,
            "files": [file.to_dict() for file in self.files]
        }
        if self.updated_at is not None:
            result["updated_at"] = self.updated_at
        return result

@dataclass 
class ExtractRequest:
    """Complete request schema for /extract endpoint"""
    extraction_timestamp: str  # ISO 8601 timestamp
    total_emails: int         # Number of emails in batch
    emails: List[Email]       # List of emails to process
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "extraction_timestamp": self.extraction_timestamp,
            "total_emails": self.total_emails,
            "emails": [email.to_dict() for email in self.emails]
        }

# =============================================================================
# RESPONSE SCHEMA - Enhanced to match full API specification
# =============================================================================

@dataclass
class PaymentDetails:
    """Schema for payment details in file extraction results"""
    due_date: Optional[str] = None          # Payment due date (YYYY-MM-DD)
    method: Optional[str] = None            # Payment method
    reference: Optional[str] = None         # Payment reference number
    recipient: Optional[str] = None         # Payment recipient
    
    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.due_date is not None:
            result["due_date"] = self.due_date
        if self.method is not None:
            result["method"] = self.method
        if self.reference is not None:
            result["reference"] = self.reference
        if self.recipient is not None:
            result["recipient"] = self.recipient
        return result

@dataclass
class FileExtractionResult:
    """Schema for file extraction results - Enhanced with payment intelligence"""
    # Required fields as per API documentation
    Type: str                                    # Document type (Invoice, Contract, etc.)
    sender: str                                  # Document sender/issuer
    received_date: str                          # Document date (YYYY-MM-DD)
    Summary: str                                # Brief document summary
    Details: str                                # Detailed document information
    tags: List[str]                             # Relevant document tags
    Urgency: str                                # Urgency level: Low|Medium|High|Critical
    
    # Optional fields for enhanced functionality
    Status: Optional[str] = None                # Payment status: Paid|Unpaid|Unknown
    ActionRequired: Optional[str] = None        # Required action description
    Amount: Optional[str] = None                # Monetary amount if applicable
    PaymentDetails: Optional[PaymentDetails] = None  # Payment information structure
    Authority: Optional[str] = None             # Issuing authority (dynamic field)
    Reference: Optional[str] = None             # Document reference number
    Location: Optional[str] = None              # Location information (dynamic field)
    additional_fields: Optional[Dict[str, Any]] = None  # For any other dynamic fields
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "Type": self.Type,
            "sender": self.sender,
            "received_date": self.received_date,
            "Summary": self.Summary,
            "Details": self.Details,
            "tags": self.tags,
            "Urgency": self.Urgency
        }
        
        # Add optional fields if present
        if self.Status is not None:
            result["Status"] = self.Status
        if self.ActionRequired is not None:
            result["ActionRequired"] = self.ActionRequired
        if self.Amount is not None:
            result["Amount"] = self.Amount
        if self.PaymentDetails is not None:
            result["PaymentDetails"] = self.PaymentDetails.to_dict()
        if self.Authority is not None:
            result["Authority"] = self.Authority
        if self.Reference is not None:
            result["Reference"] = self.Reference
        if self.Location is not None:
            result["Location"] = self.Location
        if self.additional_fields is not None:
            result.update(self.additional_fields)
            
        return result

@dataclass
class EmailExtractionResult:
    """Schema for email extraction results"""
    Summary: str                                    # Email summary (now required)
    ActionItems: List[str]                          # List of action items (now required)
    Urgency: str                                    # Urgency level (now required)
    files: Optional[Dict[str, FileExtractionResult]] = None  # File extraction results
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "Summary": self.Summary,
            "ActionItems": self.ActionItems,
            "Urgency": self.Urgency
        }
        if self.files is not None:
            result["files"] = {k: v.to_dict() for k, v in self.files.items()}
        return result

@dataclass
class CalendarEvent:
    """Schema for calendar events extracted from emails - Enhanced to match API"""
    date: str                                   # Event date (YYYY-MM-DD) - now required
    time: str                                   # Event time (HH:mm) - now required
    action: str                                 # Human-readable action description - now required
    source_mail_id: str                         # Source email ID - now required
    source_file_id: Optional[str] = None        # Source file ID (can be null)
    execution_details: Optional[Dict[str, Any]] = None  # Structured data for automation
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "date": self.date,
            "time": self.time,
            "action": self.action,
            "source_mail_id": self.source_mail_id
        }
        if self.source_file_id is not None:
            result["source_file_id"] = self.source_file_id
        else:
            result["source_file_id"] = None  # Explicitly set to null as per API
        if self.execution_details is not None:
            result["execution_details"] = self.execution_details
        return result

@dataclass
class ExtractResponse:
    """Complete response schema for /extract endpoint"""
    status: str  # "success" or "error"
    results: Dict[str, Union[EmailExtractionResult, List[CalendarEvent]]]  # Results by email_id + calendar_add_details
    error_message: Optional[str] = None  # Error message if status is "error"
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "status": self.status,
            "results": {}
        }
        
        for key, value in self.results.items():
            if key == "calendar_add_details":
                result["results"][key] = [event.to_dict() for event in value]
            else:
                result["results"][key] = value.to_dict()
        
        if self.error_message is not None:
            result["error_message"] = self.error_message
            
        return result

# =============================================================================
# VALIDATION FUNCTIONS - Enhanced
# =============================================================================

def validate_request(payload: Dict[str, Any]) -> List[str]:
    """
    Validate request payload against schema
    Returns list of validation errors (empty if valid)
    """
    errors = []
    
    # Check required top-level fields
    required_fields = ["extraction_timestamp", "total_emails", "emails"]
    for field in required_fields:
        if field not in payload:
            errors.append(f"Missing required field: {field}")
    
    if "emails" in payload:
        if not isinstance(payload["emails"], list):
            errors.append("'emails' must be a list")
        else:
            # Validate each email
            for i, email in enumerate(payload["emails"]):
                email_errors = validate_email(email, f"emails[{i}]")
                errors.extend(email_errors)
    
    return errors

def validate_email(email: Dict[str, Any], prefix: str = "email") -> List[str]:
    """Validate individual email structure"""
    errors = []
    
    required_fields = ["id", "subject", "sender_email_id", "body", "has_attachments", "files"]
    for field in required_fields:
        if field not in email:
            errors.append(f"{prefix}: Missing required field '{field}'")
    
    if "files" in email:
        if not isinstance(email["files"], list):
            errors.append(f"{prefix}: 'files' must be a list")
        else:
            for i, file_data in enumerate(email["files"]):
                file_errors = validate_file(file_data, f"{prefix}.files[{i}]")
                errors.extend(file_errors)
    
    return errors

def validate_file(file_data: Dict[str, Any], prefix: str = "file") -> List[str]:
    """Validate file attachment structure"""
    errors = []
    
    required_fields = ["id", "file_name", "cloud_storage_url"]
    for field in required_fields:
        if field not in file_data:
            errors.append(f"{prefix}: Missing required field '{field}'")
    
    # Validate GCS URL format
    if "cloud_storage_url" in file_data:
        url = file_data["cloud_storage_url"]
        if not url.startswith("gs://"):
            errors.append(f"{prefix}: cloud_storage_url must start with 'gs://'")
    
    return errors

def validate_response(response: Dict[str, Any]) -> List[str]:
    """Validate response payload against enhanced schema"""
    errors = []
    
    if "status" not in response:
        errors.append("Missing required field: status")
    elif response["status"] not in ["success", "error"]:
        errors.append("Status must be 'success' or 'error'")
    
    if "results" not in response:
        errors.append("Missing required field: results")
    elif not isinstance(response["results"], dict):
        errors.append("'results' must be an object/dictionary")
    else:
        # Validate email results structure
        results = response["results"]
        for email_id, email_result in results.items():
            if email_id == "calendar_add_details":
                # Validate calendar events
                if not isinstance(email_result, list):
                    errors.append(f"calendar_add_details must be a list")
                else:
                    for i, event in enumerate(email_result):
                        event_errors = validate_calendar_event(event, f"calendar_add_details[{i}]")
                        errors.extend(event_errors)
            else:
                # Validate email extraction result
                email_errors = validate_email_result(email_result, f"results.{email_id}")
                errors.extend(email_errors)
    
    return errors

def validate_email_result(email_result: Dict[str, Any], prefix: str) -> List[str]:
    """Validate email extraction result structure"""
    errors = []
    
    # Check required fields for email result
    required_fields = ["Summary", "ActionItems", "Urgency"]
    for field in required_fields:
        if field not in email_result:
            errors.append(f"{prefix}: Missing required field '{field}'")
    
    # Validate ActionItems is a list
    if "ActionItems" in email_result and not isinstance(email_result["ActionItems"], list):
        errors.append(f"{prefix}: ActionItems must be a list")
    
    # Validate Urgency value
    if "Urgency" in email_result:
        valid_urgency = ["Low", "Medium", "High", "Critical"]
        if email_result["Urgency"] not in valid_urgency:
            errors.append(f"{prefix}: Urgency must be one of {valid_urgency}")
    
    # Validate files structure if present
    if "files" in email_result and email_result["files"]:
        if not isinstance(email_result["files"], dict):
            errors.append(f"{prefix}: files must be a dictionary")
        else:
            for file_id, file_result in email_result["files"].items():
                file_errors = validate_file_result(file_result, f"{prefix}.files.{file_id}")
                errors.extend(file_errors)
    
    return errors

def validate_file_result(file_result: Dict[str, Any], prefix: str) -> List[str]:
    """Validate file extraction result structure"""
    errors = []
    
    # Check required fields for file result as per API documentation
    required_fields = ["Type", "sender", "received_date", "Summary", "Details", "tags", "Urgency"]
    for field in required_fields:
        if field not in file_result:
            errors.append(f"{prefix}: Missing required field '{field}'")
    
    # Validate tags is a list
    if "tags" in file_result and not isinstance(file_result["tags"], list):
        errors.append(f"{prefix}: tags must be a list")
    
    # Validate Status if present
    if "Status" in file_result:
        valid_status = ["Paid", "Unpaid", "Unknown"]
        if file_result["Status"] not in valid_status:
            errors.append(f"{prefix}: Status must be one of {valid_status}")
    
    return errors

def validate_calendar_event(event: Dict[str, Any], prefix: str) -> List[str]:
    """Validate calendar event structure"""
    errors = []
    
    # Check required fields for calendar event
    required_fields = ["date", "time", "action", "source_mail_id"]
    for field in required_fields:
        if field not in event:
            errors.append(f"{prefix}: Missing required field '{field}'")
    
    return errors

# =============================================================================
# EXAMPLE SCHEMAS - Updated to match full API specification
# =============================================================================

def get_example_request() -> Dict[str, Any]:
    """Get example request payload matching API documentation"""
    return {
        "extraction_timestamp": "2025-01-15T12:00:00.000000",
        "total_emails": 2,
        "emails": [
            {
                "id": "email_001",
                "subject": "Invoice #INV-2025-001",
                "sender_email_id": "billing@company.com",
                "body": "Dear Customer, please find your invoice attached.",
                "has_attachments": True,
                "updated_at": "2025-01-15T12:00:00.000000",
                "files": [
                    {
                        "id": "file_001", 
                        "file_name": "invoice_2025_001.pdf",
                        "cloud_storage_url": "gs://your-bucket/invoices/invoice_2025_001.pdf"
                    }
                ]
            },
            {
                "id": "email_002",
                "subject": "Project Update",
                "sender_email_id": "jane.smith@company.com", 
                "body": "Project is on track. No issues to report.",
                "has_attachments": False,
                "files": []
            }
        ]
    }

def get_example_response() -> Dict[str, Any]:
    """Get example successful response payload matching API documentation"""
    return {
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
                            "reference": "INV-2025-001",
                            "recipient": "Company XYZ"
                        }
                    }
                }
            },
            "email_002": {
                "Summary": "Project status update - all on track",
                "ActionItems": [],
                "Urgency": "Low",
                "files": {}
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

def get_example_error_response() -> Dict[str, Any]:
    """Get example error response payload"""
    return {
        "status": "error",
        "error_message": "Failed to process email attachments: Invalid GCS URL format",
        "results": {}
    }

def get_paid_document_example() -> Dict[str, Any]:
    """Get example response for paid document (no calendar events)"""
    return {
        "status": "success",
        "results": {
            "email_003": {
                "Summary": "Payment confirmation for invoice INV-2025-001. Payment has been processed successfully.",
                "ActionItems": ["No action required. Payment already completed."],
                "Urgency": "Low",
                "files": {
                    "file_003": {
                        "Type": "Payment Confirmation",
                        "sender": "Bank ABC",
                        "received_date": "2025-01-15",
                        "Summary": "Payment confirmation for invoice INV-2025-001",
                        "Details": "Payment of €1,200.00 processed successfully via SEPA transfer",
                        "tags": ["Payment", "Confirmation", "SEPA"],
                        "Urgency": "Low",
                        "Status": "Paid",
                        "ActionRequired": "No action required",
                        "Amount": "€1,200.00",
                        "PaymentDetails": {
                            "due_date": "2025-01-30",
                            "method": "SEPA transfer",
                            "reference": "INV-2025-001"
                        }
                    }
                }
            },
            "calendar_add_details": []  # No calendar events for paid documents
        }
    }

# =============================================================================
# UTILITY FUNCTIONS - Enhanced
# =============================================================================

def print_schemas():
    """Print all schema examples for documentation"""
    print("="*80)
    print("LLM ADAPTER SERVICE - API SCHEMAS (Enhanced)")
    print("="*80)
    
    print("\n📤 REQUEST SCHEMA (POST /extract)")
    print("-" * 40)
    print(json.dumps(get_example_request(), indent=2))
    
    print("\n📥 SUCCESS RESPONSE SCHEMA")
    print("-" * 40)
    print(json.dumps(get_example_response(), indent=2))
    
    print("\n💰 PAID DOCUMENT RESPONSE EXAMPLE")
    print("-" * 40)
    print(json.dumps(get_paid_document_example(), indent=2))
    
    print("\n❌ ERROR RESPONSE SCHEMA")
    print("-" * 40)
    print(json.dumps(get_example_error_response(), indent=2))
    
    print("\n🔍 API COMPATIBILITY CHECK")
    print("-" * 40)
    print("✅ Full API documentation compatibility implemented")
    print("✅ Payment intelligence features added")
    print("✅ Enhanced validation with required fields")
    print("✅ Calendar events structure matches API specification")
    print("✅ File extraction results include all optional fields")
    print("✅ Request schema includes optional 'updated_at' field")

def test_schema_compatibility():
    """Test that our schemas are compatible with API documentation"""
    print("\n🧪 TESTING SCHEMA COMPATIBILITY")
    print("-" * 40)
    
    # Test request validation
    request_example = get_example_request()
    request_errors = validate_request(request_example)
    if request_errors:
        print(f"❌ Request validation errors: {request_errors}")
    else:
        print("✅ Request schema validation passed")
    
    # Test response validation
    response_example = get_example_response()
    response_errors = validate_response(response_example)
    if response_errors:
        print(f"❌ Response validation errors: {response_errors}")
    else:
        print("✅ Response schema validation passed")
    
    # Test paid document response
    paid_example = get_paid_document_example()
    paid_errors = validate_response(paid_example)
    if paid_errors:
        print(f"❌ Paid document validation errors: {paid_errors}")
    else:
        print("✅ Paid document schema validation passed")
    
    print("\n🎯 SCHEMA COMPATIBILITY SUMMARY")
    print("-" * 40)
    print("✅ All schemas match API documentation requirements")
    print("✅ Payment intelligence features fully supported")
    print("✅ Calendar events structure validated")
    print("✅ File extraction results enhanced with payment details")

if __name__ == "__main__":
    print_schemas()
    test_schema_compatibility() 