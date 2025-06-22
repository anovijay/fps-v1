# FPS Quick Reference Guide

## 🚀 Getting Started in 5 Minutes

### 1. Setup
```python
from firestore_service import FirestoreService
fs = FirestoreService()
```

### 2. Most Common Queries

```python
# Get unpaid invoices
unpaid = fs.get_unpaid_invoices(limit=20)

# Get this month's expenses
from datetime import datetime
now = datetime.now()
expenses = fs.get_monthly_expenses(now.year, now.month)

# Get urgent items for briefing
urgent = fs.get_urgent_items_for_briefing()

# Get payments due soon
due_soon = fs.get_payment_due_soon(days_ahead=7)

# NEW: Get calendar events
calendar_events = list(fs.db.collection('calendar_events').stream())

# NEW: Get finance events
finance_events = list(fs.db.collection('finance_events').stream())
```

## 📊 Data Structure

### Key Fields You'll Use

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `document_type` | string | Document type | "Invoice", "Receipt", "Contract" |
| `sender` | string | Who sent it | "ABC Company Ltd" |
| `amount` | string | Amount with currency | "€2,500.00" |
| `payment_status` | string | Payment status | "Paid", "Unpaid", "Pending" |
| `payment_due_date` | string | When payment is due | "2025-07-15" |
| `urgency` | string | Urgency level | "Low", "Medium", "High", "Critical" |
| `is_invoice` | boolean | Is it an invoice? | `true`, `false` |
| `is_receipt` | boolean | Is it a receipt? | `true`, `false` |
| `tags` | array | Document tags | `["Invoice", "Q2", "Consulting"]` |

## 🔍 Common Use Cases

### Monthly Expense Report
```python
def get_monthly_summary(year, month):
    expenses = fs.get_monthly_expenses(year, month)
    
    total = 0
    unpaid_count = 0
    
    for expense in expenses:
        # Extract amount (basic parsing)
        amount_str = expense.get('amount', '0')
        if '€' in amount_str:
            amount = float(amount_str.replace('€', '').replace(',', ''))
            total += amount
        
        if expense.get('payment_status') == 'Unpaid':
            unpaid_count += 1
    
    return {
        'total_amount': total,
        'total_items': len(expenses),
        'unpaid_count': unpaid_count
    }

# Usage
summary = get_monthly_summary(2025, 6)
print(f"Total: €{summary['total_amount']:,.2f}")
```

### Daily Briefing
```python
def get_daily_briefing():
    urgent_items = fs.get_urgent_items_for_briefing()
    payments_due = fs.get_payment_due_soon(days_ahead=3)
    
    briefing = []
    
    # Add urgent items
    for item in urgent_items:
        briefing.append({
            'type': 'urgent',
            'message': f"🚨 {item['document_type']} from {item['sender']} - {item['urgency']}",
            'action': item.get('action_required', '')
        })
    
    # Add payment reminders
    for payment in payments_due:
        briefing.append({
            'type': 'payment',
            'message': f"💰 Payment due: {payment['amount']} to {payment['sender']}",
            'due_date': payment.get('payment_due_date', '')
        })
    
    return briefing

# Usage
briefing = get_daily_briefing()
for item in briefing:
    print(item['message'])
```

### Payment Reminders
```python
def get_payment_reminders():
    due_soon = fs.get_payment_due_soon(days_ahead=7)
    
    reminders = []
    for payment in due_soon:
        reminders.append({
            'vendor': payment.get('sender', 'Unknown'),
            'amount': payment.get('amount', 'N/A'),
            'due_date': payment.get('payment_due_date', 'N/A'),
            'reference': payment.get('payment_reference', ''),
            'method': payment.get('payment_method', 'Bank transfer')
        })
    
    return reminders

# Usage
reminders = get_payment_reminders()
for reminder in reminders:
    print(f"Pay {reminder['amount']} to {reminder['vendor']} by {reminder['due_date']}")
```

### Vendor Analysis
```python
def analyze_vendors():
    invoices = fs.get_documents_by_type("Invoice", limit=500)
    
    vendors = {}
    for invoice in invoices:
        vendor = invoice.get('sender', 'Unknown')
        
        if vendor not in vendors:
            vendors[vendor] = {
                'total_invoices': 0,
                'unpaid_invoices': 0,
                'total_amount': 0
            }
        
        vendors[vendor]['total_invoices'] += 1
        
        if invoice.get('payment_status') == 'Unpaid':
            vendors[vendor]['unpaid_invoices'] += 1
    
    return vendors

# Usage
vendors = analyze_vendors()
for vendor, stats in vendors.items():
    print(f"{vendor}: {stats['total_invoices']} invoices, {stats['unpaid_invoices']} unpaid")
```

### Calendar Events
```python
def get_upcoming_calendar_events(days=7):
    from datetime import datetime, timedelta
    
    today = datetime.now().strftime("%Y-%m-%d")
    future = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    
    events = list(
        fs.db.collection('calendar_events')
        .where("date", ">=", today)
        .where("date", "<=", future)
        .order_by("date")
        .stream()
    )
    
    return [event.to_dict() for event in events]

# Usage
upcoming = get_upcoming_calendar_events(days=14)
for event in upcoming:
    print(f"📅 {event['date']} at {event['time']}: {event['action']}")
```

### Finance Events Summary
```python
def get_finance_summary(category=None):
    query = fs.db.collection('finance_events')
    
    if category:
        query = query.where("category", "==", category)
    
    events = list(query.stream())
    
    total_expenses = 0
    total_income = 0
    
    for event_doc in events:
        event = event_doc.to_dict()
        amount = float(event.get('amount', '0'))
        
        if event.get('type') == 'Expense':
            total_expenses += amount
        elif event.get('type') == 'Income':
            total_income += amount
    
    return {
        'total_expenses': total_expenses,
        'total_income': total_income,
        'net': total_income - total_expenses,
        'count': len(events)
    }

# Usage
all_finance = get_finance_summary()
travel_finance = get_finance_summary(category="Travel")
print(f"Total expenses: €{all_finance['total_expenses']}")
print(f"Travel expenses: €{travel_finance['total_expenses']}")
```

## ⚡ Quick Filters

### Filter by Document Type
```python
# Get only invoices
invoices = fs.get_documents_by_type("Invoice")

# Get only receipts  
receipts = fs.get_documents_by_type("Receipt")

# Get only contracts
contracts = fs.get_documents_by_type("Contract")
```

### Filter by Status
```python
# Get unpaid invoices
unpaid = fs.get_unpaid_invoices()

# Get urgent items
urgent = fs.get_urgent_items_for_briefing(urgency_levels=["High", "Critical"])
```

### Filter by Time
```python
# This month's expenses
from datetime import datetime
now = datetime.now()
this_month = fs.get_monthly_expenses(now.year, now.month)

# Last month's expenses
last_month = now.month - 1 if now.month > 1 else 12
last_year = now.year if now.month > 1 else now.year - 1
last_month_expenses = fs.get_monthly_expenses(last_year, last_month)

# Payments due in next 3 days
due_soon = fs.get_payment_due_soon(days_ahead=3)
```

## 🛠️ Utility Functions

### Extract Amount from String
```python
import re

def extract_amount(amount_str):
    """Extract numeric amount from string like '€2,500.00'"""
    if not amount_str:
        return 0.0
    
    # Remove currency symbols and extract numbers
    numbers = re.findall(r'[\d,]+\.?\d*', amount_str)
    if numbers:
        return float(numbers[0].replace(',', ''))
    return 0.0

# Usage
amount = extract_amount("€2,500.00")  # Returns 2500.0
```

### Format Currency
```python
def format_currency(amount, currency="€"):
    """Format amount as currency"""
    return f"{currency}{amount:,.2f}"

# Usage
formatted = format_currency(2500.0)  # Returns "€2,500.00"
```

### Check Document Type
```python
def is_financial_document(doc):
    """Check if document is financial (invoice, receipt, bill)"""
    return doc.get('is_invoice') or doc.get('is_receipt') or doc.get('is_bill')

def is_urgent(doc):
    """Check if document is urgent"""
    return doc.get('urgency') in ['High', 'Critical']

def is_overdue(doc):
    """Check if payment is overdue (basic check)"""
    from datetime import datetime
    
    due_date_str = doc.get('payment_due_date')
    if not due_date_str:
        return False
    
    try:
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
        return due_date < datetime.now() and doc.get('payment_status') == 'Unpaid'
    except:
        return False
```

## 🚨 Error Handling

### Safe Query Wrapper
```python
def safe_query(query_func, *args, **kwargs):
    """Safely execute a query with error handling"""
    try:
        return query_func(*args, **kwargs)
    except Exception as e:
        if "requires an index" in str(e):
            print("⚠️ Firestore index needed. Check Google Cloud Console.")
            return []
        else:
            print(f"❌ Query error: {e}")
            return []

# Usage
unpaid_invoices = safe_query(fs.get_unpaid_invoices, limit=50)
```

### Check Data Availability
```python
def check_data_availability():
    """Check if FPS has processed any data"""
    try:
        # Try to get any document from the collection
        db = fs.db
        docs = list(db.collection('file_extraction_results').limit(1).stream())
        
        if docs:
            print(f"✅ Data available: {len(docs)} sample documents found")
            return True
        else:
            print("⚠️ No data available. FPS may not have processed any emails yet.")
            return False
    except Exception as e:
        print(f"❌ Error checking data: {e}")
        return False

# Usage
if check_data_availability():
    # Proceed with queries
    pass
```

## 📝 Integration Patterns

### Service Base Class
```python
class FPSIntegrationService:
    def __init__(self):
        self.fs = FirestoreService()
        self._cache = {}
    
    def get_cached_data(self, key, fetch_func, cache_minutes=30):
        """Get data with caching"""
        import time
        
        now = time.time()
        if key in self._cache:
            cached_time, cached_data = self._cache[key]
            if now - cached_time < cache_minutes * 60:
                return cached_data
        
        # Fetch fresh data
        data = fetch_func()
        self._cache[key] = (now, data)
        return data
    
    def clear_cache(self):
        """Clear all cached data"""
        self._cache.clear()

# Usage
class ExpenseService(FPSIntegrationService):
    def get_monthly_expenses(self, year, month):
        cache_key = f"expenses_{year}_{month}"
        return self.get_cached_data(
            cache_key, 
            lambda: self.fs.get_monthly_expenses(year, month)
        )
```

### Batch Processing Pattern
```python
def process_documents_in_batches(documents, batch_size=50):
    """Process documents in batches to avoid memory issues"""
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        yield batch

# Usage
all_invoices = fs.get_documents_by_type("Invoice", limit=1000)
for batch in process_documents_in_batches(all_invoices):
    # Process each batch
    for invoice in batch:
        # Process individual invoice
        pass
```

## 🔗 Environment Setup

### Minimal Setup
```python
import os
from google.cloud import firestore

# Set environment variables
os.environ['GOOGLE_CLOUD_PROJECT'] = 'rhea-461313'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/path/to/key.json'

# Initialize Firestore
db = firestore.Client()
```

### Development vs Production
```python
import os

def get_firestore_client():
    if os.getenv('ENVIRONMENT') == 'development':
        # Use emulator for development
        os.environ['FIRESTORE_EMULATOR_HOST'] = 'localhost:8080'
        return firestore.Client(project='demo-project')
    else:
        # Use production Firestore
        return firestore.Client()
```

## 📚 Common Queries Cheat Sheet

```python
# All available methods
fs.get_unpaid_invoices(limit=50)
fs.get_monthly_expenses(year, month)
fs.get_urgent_items_for_briefing(urgency_levels=["High", "Critical"])
fs.get_documents_by_type(document_type, limit=50)
fs.get_payment_due_soon(days_ahead=7)

# Direct Firestore queries (if you need custom filtering)
db = fs.db
collection = db.collection('file_extraction_results')

# Simple filters
invoices = collection.where('is_invoice', '==', True).limit(10).stream()
urgent_docs = collection.where('urgency', '==', 'High').limit(10).stream()
specific_vendor = collection.where('sender', '==', 'ABC Company').limit(10).stream()

# Get all documents (use with caution)
all_docs = collection.limit(100).stream()
```

---

## 🆘 Need Help?

1. **Check if data exists**: Run `check_data_availability()`
2. **Test connection**: Run `fs.test_connection()`
3. **Start simple**: Use `fs.get_documents_by_type("Invoice", limit=5)`
4. **Check indexes**: Complex queries need Firestore indexes (follow error URLs)
5. **Review logs**: Check FPS processing logs for issues

**Happy coding! 🚀** 