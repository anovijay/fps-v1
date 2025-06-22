# FPS Developer Integration Guide

## Overview

This guide is for development teams building services that consume structured file extraction data from the FPS (Email Processing Service). The FPS processes emails with attachments and extracts structured data that can be easily queried by other services for expense tracking, daily briefings, calendar events, and more.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Data Architecture](#data-architecture)
3. [Available Query Methods](#available-query-methods)
4. [Integration Examples](#integration-examples)
5. [Data Schemas](#data-schemas)
6. [Best Practices](#best-practices)
7. [Error Handling](#error-handling)
8. [Performance Considerations](#performance-considerations)
9. [Troubleshooting](#troubleshooting)

## Quick Start

### Installation

```bash
pip install google-cloud-firestore==2.18.0
```

### Basic Setup

```python
from google.cloud import firestore
from firestore_service import FirestoreService

# Initialize the service
fs = FirestoreService()

# Test connection
if fs.test_connection():
    print("✅ Connected to Firestore")
else:
    print("❌ Connection failed")
```

### Your First Query

```python
# Get all unpaid invoices
unpaid_invoices = fs.get_unpaid_invoices(limit=10)

for invoice in unpaid_invoices:
    print(f"Invoice: {invoice['amount']} from {invoice['sender']}")
    print(f"Due: {invoice['payment_due_date']}")
```

## Data Architecture

### Collections Overview

The FPS system uses two main collections for extraction results:

| Collection | Purpose | Use Case |
|------------|---------|----------|
| `extraction_results` | Email-level summaries | Backward compatibility, email overviews |
| `file_extraction_results` | **Structured file data** | **Your primary data source** |

### Why Use `file_extraction_results`?

❌ **Old way** (hard to query):
```json
{
  "files": {
    "file_123": "{\"Type\":\"Invoice\",\"Amount\":\"€1,200\"...}"
  }
}
```

✅ **New way** (easy to query):
```json
{
  "document_type": "Invoice",
  "amount": "€1,200",
  "payment_status": "Unpaid",
  "payment_due_date": "2025-07-15",
  "is_invoice": true
}
```

## Available Query Methods

### 1. Expense Tracking Methods

#### `get_unpaid_invoices(limit=50)`
Get all unpaid invoices for expense tracking.

```python
unpaid_invoices = fs.get_unpaid_invoices(limit=20)
```

**Returns:** List of invoice documents with `payment_status == "Unpaid"`

#### `get_monthly_expenses(year, month)`
Get all expenses for a specific month.

```python
# Get June 2025 expenses
expenses = fs.get_monthly_expenses(2025, 6)
```

**Returns:** List of expense documents for the specified month

#### `get_payment_due_soon(days_ahead=7)`
Get invoices with payments due within specified days.

```python
# Get payments due in next 7 days
due_soon = fs.get_payment_due_soon(days_ahead=7)
```

**Returns:** List of invoices with upcoming due dates

### 2. Daily Briefing Methods

#### `get_urgent_items_for_briefing(urgency_levels=["High", "Critical"])`
Get urgent items for daily briefings.

```python
urgent_items = fs.get_urgent_items_for_briefing()
```

**Returns:** List of urgent documents for briefing

### 3. Document Management Methods

#### `get_documents_by_type(document_type, limit=50)`
Get documents by type for categorization.

```python
invoices = fs.get_documents_by_type("Invoice", limit=10)
receipts = fs.get_documents_by_type("Receipt", limit=10)
contracts = fs.get_documents_by_type("Contract", limit=10)
```

**Returns:** List of documents of the specified type

## Integration Examples

### 1. Monthly Expense Tracking Service

```python
class MonthlyExpenseTracker:
    def __init__(self):
        self.fs = FirestoreService()
    
    def generate_monthly_report(self, year: int, month: int):
        """Generate monthly expense report"""
        
        # Get all expenses for the month
        expenses = self.fs.get_monthly_expenses(year, month)
        
        report = {
            'month': f"{year}-{month:02d}",
            'total_amount': 0,
            'total_items': len(expenses),
            'by_category': {},
            'unpaid_items': [],
            'urgent_items': []
        }
        
        for expense in expenses:
            # Calculate total amount
            amount_str = expense.get('amount', '0')
            amount_value = self.extract_amount(amount_str)
            report['total_amount'] += amount_value
            
            # Categorize by document type
            doc_type = expense.get('document_type', 'Other')
            if doc_type not in report['by_category']:
                report['by_category'][doc_type] = {
                    'count': 0,
                    'total_amount': 0
                }
            report['by_category'][doc_type]['count'] += 1
            report['by_category'][doc_type]['total_amount'] += amount_value
            
            # Track unpaid items
            if expense.get('payment_status') == 'Unpaid':
                report['unpaid_items'].append({
                    'sender': expense.get('sender'),
                    'amount': expense.get('amount'),
                    'due_date': expense.get('payment_due_date'),
                    'reference': expense.get('payment_reference')
                })
            
            # Track urgent items
            if expense.get('urgency') in ['High', 'Critical']:
                report['urgent_items'].append({
                    'sender': expense.get('sender'),
                    'urgency': expense.get('urgency'),
                    'action_required': expense.get('action_required')
                })
        
        return report
    
    def extract_amount(self, amount_str: str) -> float:
        """Extract numeric amount from string"""
        import re
        if not amount_str:
            return 0.0
        
        # Remove currency symbols and extract numbers
        numbers = re.findall(r'[\d,]+\.?\d*', amount_str)
        if numbers:
            return float(numbers[0].replace(',', ''))
        return 0.0

# Usage
tracker = MonthlyExpenseTracker()
report = tracker.generate_monthly_report(2025, 6)
print(f"Total expenses: €{report['total_amount']:,.2f}")
```

### 2. Daily Briefing Service

```python
from datetime import datetime

class DailyBriefingService:
    def __init__(self):
        self.fs = FirestoreService()
    
    def generate_daily_briefing(self):
        """Generate daily briefing with urgent items and due payments"""
        
        briefing = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'urgent_items': [],
            'payments_due_soon': [],
            'summary': {}
        }
        
        # Get urgent items
        urgent_items = self.fs.get_urgent_items_for_briefing()
        for item in urgent_items:
            briefing['urgent_items'].append({
                'type': item.get('document_type', 'Document'),
                'sender': item.get('sender', 'Unknown'),
                'urgency': item.get('urgency', 'Unknown'),
                'summary': item.get('summary', ''),
                'action_required': item.get('action_required', ''),
                'amount': item.get('amount', '') if item.get('is_invoice') else None
            })
        
        # Get payments due soon
        payments_due = self.fs.get_payment_due_soon(days_ahead=3)
        for payment in payments_due:
            briefing['payments_due_soon'].append({
                'sender': payment.get('sender', 'Unknown'),
                'amount': payment.get('amount', 'N/A'),
                'due_date': payment.get('payment_due_date', 'N/A'),
                'reference': payment.get('payment_reference', ''),
                'urgency': payment.get('urgency', 'Normal')
            })
        
        # Generate summary
        briefing['summary'] = {
            'urgent_items_count': len(briefing['urgent_items']),
            'payments_due_count': len(briefing['payments_due_soon']),
            'critical_items': len([i for i in urgent_items if i.get('urgency') == 'Critical']),
            'high_priority_items': len([i for i in urgent_items if i.get('urgency') == 'High'])
        }
        
        return briefing
    
    def format_briefing_email(self, briefing):
        """Format briefing as email content"""
        
        email_content = f"""
# Daily Briefing - {briefing['date']}

## Summary
- 🚨 Urgent Items: {briefing['summary']['urgent_items_count']}
- 💰 Payments Due Soon: {briefing['summary']['payments_due_count']}
- 🔥 Critical Items: {briefing['summary']['critical_items']}

## Urgent Items Requiring Attention
"""
        
        for item in briefing['urgent_items']:
            urgency_emoji = "🔥" if item['urgency'] == "Critical" else "⚠️"
            email_content += f"""
{urgency_emoji} **{item['type']}** from {item['sender']}
   - Urgency: {item['urgency']}
   - Action: {item['action_required']}
"""
            if item.get('amount'):
                email_content += f"   - Amount: {item['amount']}\n"
        
        if briefing['payments_due_soon']:
            email_content += "\n## Payments Due Soon\n"
            for payment in briefing['payments_due_soon']:
                email_content += f"""
💳 **{payment['sender']}**
   - Amount: {payment['amount']}
   - Due Date: {payment['due_date']}
   - Reference: {payment['reference']}
"""
        
        return email_content

# Usage
briefing_service = DailyBriefingService()
briefing = briefing_service.generate_daily_briefing()
email_content = briefing_service.format_briefing_email(briefing)
```

### 3. Calendar Event Service

```python
from datetime import datetime, timedelta

class CalendarEventService:
    def __init__(self):
        self.fs = FirestoreService()
    
    def create_payment_reminders(self, days_ahead=7):
        """Create calendar events for upcoming payment due dates"""
        
        payments_due = self.fs.get_payment_due_soon(days_ahead=days_ahead)
        calendar_events = []
        
        for payment in payments_due:
            due_date = payment.get('payment_due_date')
            if not due_date:
                continue
            
            # Create reminder event 2 days before due date
            reminder_date = self.calculate_reminder_date(due_date, days_before=2)
            
            event = {
                'title': f"Payment Due: {payment.get('sender', 'Unknown')}",
                'date': reminder_date,
                'time': '09:00',
                'description': f"""
Payment Reminder:
- Amount: {payment.get('amount', 'N/A')}
- Due Date: {due_date}
- Reference: {payment.get('payment_reference', 'N/A')}
- Method: {payment.get('payment_method', 'N/A')}
""",
                'category': 'payment_reminder',
                'source_email_id': payment.get('email_id'),
                'source_file_id': payment.get('file_id')
            }
            calendar_events.append(event)
        
        return calendar_events
    
    def create_contract_deadlines(self):
        """Create calendar events for contract-related deadlines"""
        
        contracts = self.fs.get_documents_by_type("Contract", limit=50)
        calendar_events = []
        
        for contract in contracts:
            # Look for deadline information in contract details
            details = contract.get('details', '').lower()
            
            # Simple deadline detection (you can enhance this)
            if 'deadline' in details or 'due' in details:
                event = {
                    'title': f"Contract Deadline: {contract.get('sender', 'Unknown')}",
                    'date': self.extract_deadline_from_details(contract.get('details', '')),
                    'time': '10:00',
                    'description': f"""
Contract Deadline:
- From: {contract.get('sender', 'Unknown')}
- Reference: {contract.get('reference', 'N/A')}
- Details: {contract.get('summary', 'N/A')}
""",
                    'category': 'contract_deadline',
                    'source_email_id': contract.get('email_id'),
                    'source_file_id': contract.get('file_id')
                }
                calendar_events.append(event)
        
        return calendar_events
    
    def calculate_reminder_date(self, due_date_str: str, days_before: int = 2):
        """Calculate reminder date X days before due date"""
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
            reminder_date = due_date - timedelta(days=days_before)
            return reminder_date.strftime('%Y-%m-%d')
        except:
            return due_date_str
    
    def extract_deadline_from_details(self, details: str):
        """Extract deadline date from contract details"""
        import re
        
        # Look for date patterns in details
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
            r'\d{2}-\d{2}-\d{4}'   # DD-MM-YYYY
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, details)
            if matches:
                return matches[0]
        
        # Default to 30 days from now if no date found
        default_date = datetime.now() + timedelta(days=30)
        return default_date.strftime('%Y-%m-%d')

# Usage
calendar_service = CalendarEventService()
payment_reminders = calendar_service.create_payment_reminders()
contract_deadlines = calendar_service.create_contract_deadlines()
```

### 4. Expense Analytics Service

```python
class ExpenseAnalyticsService:
    def __init__(self):
        self.fs = FirestoreService()
    
    def get_spending_trends(self, months_back=6):
        """Analyze spending trends over multiple months"""
        current_date = datetime.now()
        trends = []
        
        for i in range(months_back):
            # Calculate month/year for each period
            target_date = current_date - timedelta(days=30 * i)
            year = target_date.year
            month = target_date.month
            
            # Get expenses for this month
            expenses = self.fs.get_monthly_expenses(year, month)
            
            month_data = {
                'period': f"{year}-{month:02d}",
                'total_amount': 0,
                'invoice_count': 0,
                'receipt_count': 0,
                'unpaid_count': 0,
                'categories': {}
            }
            
            for expense in expenses:
                # Calculate amounts
                amount = self.extract_amount(expense.get('amount', '0'))
                month_data['total_amount'] += amount
                
                # Count by type
                if expense.get('is_invoice'):
                    month_data['invoice_count'] += 1
                if expense.get('is_receipt'):
                    month_data['receipt_count'] += 1
                if expense.get('payment_status') == 'Unpaid':
                    month_data['unpaid_count'] += 1
                
                # Categorize by sender/vendor
                sender = expense.get('sender', 'Unknown')
                if sender not in month_data['categories']:
                    month_data['categories'][sender] = 0
                month_data['categories'][sender] += amount
            
            trends.append(month_data)
        
        return trends
    
    def get_vendor_analysis(self):
        """Analyze spending by vendor"""
        
        # Get all invoices (you might want to limit this by date range)
        invoices = self.fs.get_documents_by_type("Invoice", limit=1000)
        
        vendor_analysis = {}
        
        for invoice in invoices:
            sender = invoice.get('sender', 'Unknown')
            amount = self.extract_amount(invoice.get('amount', '0'))
            
            if sender not in vendor_analysis:
                vendor_analysis[sender] = {
                    'total_amount': 0,
                    'invoice_count': 0,
                    'unpaid_amount': 0,
                    'unpaid_count': 0,
                    'average_amount': 0
                }
            
            vendor_analysis[sender]['total_amount'] += amount
            vendor_analysis[sender]['invoice_count'] += 1
            
            if invoice.get('payment_status') == 'Unpaid':
                vendor_analysis[sender]['unpaid_amount'] += amount
                vendor_analysis[sender]['unpaid_count'] += 1
        
        # Calculate averages
        for vendor, data in vendor_analysis.items():
            if data['invoice_count'] > 0:
                data['average_amount'] = data['total_amount'] / data['invoice_count']
        
        return vendor_analysis
    
    def extract_amount(self, amount_str: str) -> float:
        """Extract numeric amount from string"""
        import re
        if not amount_str:
            return 0.0
        
        numbers = re.findall(r'[\d,]+\.?\d*', amount_str)
        if numbers:
            return float(numbers[0].replace(',', ''))
        return 0.0

# Usage
analytics = ExpenseAnalyticsService()
trends = analytics.get_spending_trends(months_back=6)
vendor_analysis = analytics.get_vendor_analysis()
```

## Data Schemas

### File Extraction Result Document

```python
{
    # Reference fields
    "email_id": "email_123",
    "file_id": "file_456",
    
    # Core extraction fields
    "document_type": "Invoice",        # "Invoice", "Receipt", "Contract", "Bill", etc.
    "sender": "ABC Company Ltd",       # Sender/vendor name
    "received_date": "2025-06-22",     # Date document was received (YYYY-MM-DD)
    "summary": "Consulting services invoice",  # Brief summary
    "details": "Professional consulting services...",  # Detailed description
    "tags": ["Invoice", "Consulting", "Q2"],  # List of tags
    "urgency": "High",                 # "Low", "Medium", "High", "Critical"
    
    # Financial fields (for expense tracking)
    "payment_status": "Unpaid",        # "Paid", "Unpaid", "Pending", "Overdue"
    "action_required": "Make payment by due date",  # Required action
    "amount": "€2,500.00",            # Amount as string (includes currency)
    
    # Payment details (flattened for easy querying)
    "payment_due_date": "2025-07-15", # Due date (YYYY-MM-DD)
    "payment_method": "Bank transfer", # Payment method
    "payment_reference": "INV-2025-001", # Reference number
    "payment_recipient": "ABC Company Ltd", # Who to pay
    
    # Document categorization (boolean flags for easy filtering)
    "is_invoice": true,               # True if document is an invoice
    "is_receipt": false,              # True if document is a receipt
    "is_contract": false,             # True if document is a contract
    "is_bill": false,                 # True if document is a bill
    
    # Additional fields
    "authority": "Finance Department", # Issuing authority
    "reference": "INV-2025-001",      # Document reference
    "location": "London Office",       # Location if applicable
    
    # Timestamps
    "extracted_at": "2025-06-22T14:53:13Z", # When data was extracted
    "created_at": "2025-06-22T14:53:13Z",   # When document was created
    
    # Backward compatibility
    "original_data": { ... }          # Original extraction result
}
```

### Email Extraction Result Document (for context)

```python
{
    "email_id": "email_123",
    "summary": "Email contains invoice for consulting services",
    "action_items": ["Pay invoice by due date", "File for expense tracking"],
    "urgency": "High",
    "has_files": true,
    "files_count": 2,
    "files": { ... },                 # Original file results (kept for compatibility)
    "extracted_at": "2025-06-22T14:53:13Z",
    "created_at": "2025-06-22T14:53:13Z"
}
```

## Best Practices

### 1. Error Handling

Always handle potential errors when querying:

```python
def safe_query_unpaid_invoices():
    try:
        invoices = fs.get_unpaid_invoices(limit=50)
        return invoices
    except Exception as e:
        if "requires an index" in str(e):
            print("Firestore index needed. Check console for index creation link.")
            return []
        else:
            print(f"Query error: {e}")
            return []
```

### 2. Pagination for Large Datasets

```python
def get_all_invoices_paginated():
    all_invoices = []
    last_doc = None
    
    while True:
        query = fs.db.collection('file_extraction_results') \
                     .where('is_invoice', '==', True) \
                     .limit(100)
        
        if last_doc:
            query = query.start_after(last_doc)
        
        docs = list(query.stream())
        if not docs:
            break
        
        for doc in docs:
            all_invoices.append(doc.to_dict())
        
        last_doc = docs[-1]
    
    return all_invoices
```

### 3. Caching for Performance

```python
import time

class CachedFirestoreService:
    def __init__(self):
        self.fs = FirestoreService()
        self._cache_timestamp = {}
        self._cached_data = {}
    
    def get_monthly_expenses_cached(self, year, month, cache_minutes=30):
        cache_key = f"expenses_{year}_{month}"
        now = time.time()
        
        # Check if cache is still valid
        if (cache_key in self._cache_timestamp and 
            now - self._cache_timestamp[cache_key] < cache_minutes * 60):
            return self._cached_data.get(cache_key, [])
        
        # Fetch fresh data
        expenses = self.fs.get_monthly_expenses(year, month)
        
        # Update cache
        self._cached_data[cache_key] = expenses
        self._cache_timestamp[cache_key] = now
        
        return expenses
```

## Error Handling

### Common Errors and Solutions

#### 1. Index Required Error

**Error:** `400 The query requires an index`

**Solution:** 
- Click the provided URL in the error message
- Google Cloud Console will create the required index
- Wait 5-10 minutes for index to build

#### 2. Permission Denied

**Error:** `403 Permission denied`

**Solution:**
- Ensure your service account has Firestore read permissions
- Check that `GOOGLE_APPLICATION_CREDENTIALS` is set correctly

#### 3. Empty Results

**Issue:** Query returns empty results

**Debugging:**
```python
# Check if collection exists and has data
def debug_collection():
    db = firestore.Client()
    
    # Count total documents
    docs = list(db.collection('file_extraction_results').limit(5).stream())
    print(f"Total sample documents: {len(docs)}")
    
    # Show sample document structure
    if docs:
        sample = docs[0].to_dict()
        print("Sample document fields:")
        for key, value in sample.items():
            print(f"  {key}: {type(value)} = {value}")
```

## Performance Considerations

### 1. Query Optimization

- Use composite indexes for complex queries
- Limit results with `.limit()` parameter
- Use pagination for large datasets
- Cache frequently accessed data

### 2. Firestore Limits

- **Reads per second:** 10,000
- **Writes per second:** 10,000  
- **Document size:** 1 MB max
- **Query results:** 1 MB max

### 3. Cost Optimization

```python
# Efficient: Query with limits
expenses = fs.get_monthly_expenses(2025, 6)  # Uses date range

# Inefficient: Scanning all documents
all_docs = list(db.collection('file_extraction_results').stream())
```

## API Reference Summary

### FirestoreService Methods

| Method | Purpose | Parameters | Returns |
|--------|---------|------------|---------|
| `get_unpaid_invoices(limit)` | Get unpaid invoices | `limit: int = 50` | `List[Dict]` |
| `get_monthly_expenses(year, month)` | Get monthly expenses | `year: int, month: int` | `List[Dict]` |
| `get_urgent_items_for_briefing(urgency_levels)` | Get urgent items | `urgency_levels: List[str]` | `List[Dict]` |
| `get_documents_by_type(doc_type, limit)` | Get documents by type | `doc_type: str, limit: int` | `List[Dict]` |
| `get_payment_due_soon(days_ahead)` | Get upcoming payments | `days_ahead: int = 7` | `List[Dict]` |

### Document Fields Reference

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `document_type` | string | Type of document | "Invoice", "Receipt" |
| `sender` | string | Sender/vendor name | "ABC Company Ltd" |
| `amount` | string | Amount with currency | "€2,500.00" |
| `payment_status` | string | Payment status | "Paid", "Unpaid" |
| `payment_due_date` | string | Due date | "2025-07-15" |
| `urgency` | string | Urgency level | "Low", "High", "Critical" |
| `is_invoice` | boolean | Is this an invoice? | `true`, `false` |
| `tags` | array | Document tags | `["Invoice", "Q2"]` |

## Environment Setup

### Required Environment Variables

```bash
# Google Cloud Configuration
export GOOGLE_CLOUD_PROJECT="rhea-461313"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"

# Optional: Firestore emulator for testing
export FIRESTORE_EMULATOR_HOST="localhost:8080"
```

## Troubleshooting

### Debug Checklist

1. **Connection Issues**
   ```python
   # Test Firestore connection
   if not fs.test_connection():
       print("❌ Firestore connection failed")
   ```

2. **Missing Data**
   ```python
   # Check if FPS has processed any emails
   db = firestore.Client()
   extraction_docs = list(db.collection('extraction_results').limit(1).stream())
   if not extraction_docs:
       print("No emails have been processed by FPS yet")
   ```

3. **Index Issues**
   ```python
   # Try simple queries first
   try:
       docs = list(db.collection('file_extraction_results')
                    .where('document_type', '==', 'Invoice')
                    .limit(1).stream())
       print(f"Simple query works: {len(docs)} results")
   except Exception as e:
       print(f"Simple query failed: {e}")
   ```

---

## Support

For technical support or questions about this integration:

1. **Check the troubleshooting section** above
2. **Review FPS logs** for processing issues  
3. **Verify Firestore permissions** and indexes
4. **Test with simple queries** before complex ones

Happy coding! 🚀 