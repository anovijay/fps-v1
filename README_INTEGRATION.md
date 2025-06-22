# FPS Integration Documentation

## Overview

This directory contains comprehensive documentation and examples for integrating with the FPS (Email Processing Service) structured data. The FPS processes emails with attachments and extracts structured data that can be easily queried by other services.

## 📚 Documentation Files

### 1. **DEVELOPER_INTEGRATION_GUIDE.md** - Complete Developer Guide
- **What it is:** Comprehensive 400+ line guide with everything developers need
- **Use it for:** Full integration implementation with detailed examples
- **Contains:**
  - Complete API reference
  - 4 detailed service integration examples (expense tracking, daily briefings, calendar events, analytics)
  - Data schemas and field reference
  - Error handling patterns
  - Performance optimization tips
  - Troubleshooting guide

### 2. **QUICK_REFERENCE_GUIDE.md** - Fast Reference
- **What it is:** Quick reference for developers who need fast answers
- **Use it for:** Looking up common queries and patterns quickly
- **Contains:**
  - 5-minute quick start
  - Common use cases with code snippets
  - Utility functions
  - Cheat sheet of all available methods

### 3. **integration_examples.py** - Runnable Examples
- **What it is:** Executable Python script demonstrating integrations
- **Use it for:** Testing your setup and seeing live examples
- **Run with:** `python integration_examples.py`

## 🚀 Quick Start (2 Minutes)

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

## 🎯 Use Cases by Service Type

### Monthly Expense Tracking Service
- **Primary method:** `fs.get_monthly_expenses(year, month)`
- **Also use:** `fs.get_unpaid_invoices()` for outstanding payments
- **Documentation:** See "Monthly Expense Tracking Service" in DEVELOPER_INTEGRATION_GUIDE.md

### Daily Briefing Service  
- **Primary methods:** `fs.get_urgent_items_for_briefing()`, `fs.get_payment_due_soon()`
- **Documentation:** See "Daily Briefing Service" in DEVELOPER_INTEGRATION_GUIDE.md

### Calendar Event Service
- **Primary method:** `fs.get_payment_due_soon(days_ahead=14)` for payment reminders
- **Also use:** `fs.get_documents_by_type("Contract")` for contract deadlines
- **Documentation:** See "Calendar Event Service" in DEVELOPER_INTEGRATION_GUIDE.md

### Expense Analytics Service
- **Primary methods:** `fs.get_documents_by_type("Invoice")`, `fs.get_monthly_expenses()`
- **Documentation:** See "Expense Analytics Service" in DEVELOPER_INTEGRATION_GUIDE.md

## 📊 Data Structure Overview

The FPS system stores structured data in **four main collections**:

### Collections
- **`file_extraction_results`** - Structured file data (invoices, receipts, contracts)
- **`calendar_events`** - Calendar events extracted from emails (deliveries, check-ins, reminders)
- **`finance_events`** - Financial transactions (expenses, income, refunds)
- **`extraction_results`** - Email-level summaries (backward compatibility)

### File Extraction Results
Each document in `file_extraction_results` represents a processed file with these key fields:

### Essential Fields
- `document_type`: "Invoice", "Receipt", "Contract", "Bill"
- `sender`: Vendor/sender name
- `amount`: Amount with currency (e.g., "€2,500.00")
- `payment_status`: "Paid", "Unpaid", "Pending", "Overdue"
- `payment_due_date`: Due date in YYYY-MM-DD format
- `urgency`: "Low", "Medium", "High", "Critical"

### Boolean Flags (for easy filtering)
- `is_invoice`: true/false
- `is_receipt`: true/false  
- `is_contract`: true/false
- `is_bill`: true/false

## 🔧 Available Query Methods

| Method | Purpose | Returns |
|--------|---------|---------|
| `get_unpaid_invoices(limit=50)` | Get unpaid invoices | List of unpaid invoice documents |
| `get_monthly_expenses(year, month)` | Get monthly expenses | List of expense documents for month |
| `get_urgent_items_for_briefing()` | Get urgent items | List of high/critical priority documents |
| `get_documents_by_type(type, limit=50)` | Get docs by type | List of documents of specified type |
| `get_payment_due_soon(days_ahead=7)` | Get upcoming payments | List of invoices due within X days |

## ⚡ Quick Examples

### Get Monthly Summary
```python
def get_monthly_summary(year, month):
    expenses = fs.get_monthly_expenses(year, month)
    
    total = sum(extract_amount(exp.get('amount', '0')) for exp in expenses)
    unpaid = len([exp for exp in expenses if exp.get('payment_status') == 'Unpaid'])
    
    return {
        'total_amount': total,
        'total_items': len(expenses),
        'unpaid_count': unpaid
    }
```

### Generate Daily Briefing
```python
def get_daily_briefing():
    urgent = fs.get_urgent_items_for_briefing()
    due_soon = fs.get_payment_due_soon(days_ahead=3)
    
    return {
        'urgent_count': len(urgent),
        'payments_due_count': len(due_soon),
        'urgent_items': [f"{item['document_type']} from {item['sender']}" for item in urgent[:5]]
    }
```

## 🚨 Common Issues & Solutions

### 1. "requires an index" Error
- **Solution:** Click the URL in the error message to create the Firestore index
- **Wait time:** 5-10 minutes for index to build

### 2. Empty Results
- **Check:** Has FPS processed any emails yet?
- **Debug:** Run `integration_examples.py` to test data availability

### 3. Connection Issues
- **Check:** `GOOGLE_APPLICATION_CREDENTIALS` environment variable
- **Test:** Run `fs.test_connection()`

## 📋 Integration Checklist

- [ ] Install dependencies: `pip install google-cloud-firestore==2.18.0`
- [ ] Set up service account credentials
- [ ] Test connection with `fs.test_connection()`
- [ ] Check data availability with sample queries
- [ ] Implement error handling for index requirements
- [ ] Add caching for frequently accessed data
- [ ] Monitor performance and optimize queries

## 🔗 Environment Setup

```bash
# Required environment variables
export GOOGLE_CLOUD_PROJECT="rhea-461313"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

## 📞 Getting Help

1. **Start here:** Run `python integration_examples.py` to test your setup
2. **Quick answers:** Check QUICK_REFERENCE_GUIDE.md
3. **Detailed implementation:** See DEVELOPER_INTEGRATION_GUIDE.md
4. **Data issues:** Verify FPS has processed emails and Firestore indexes exist

## 🎉 Success Stories

The structured data approach solves the key problem where other services couldn't easily query specific information. Now:

- **Monthly expense service** can easily get `get_monthly_expenses(2025, 6)`
- **Daily briefing service** can get `get_urgent_items_for_briefing()`
- **Expense tracking** can find `get_unpaid_invoices()`
- **Payment reminders** can use `get_payment_due_soon()`

All while maintaining full backward compatibility with the original system.

---

**Happy integrating! 🚀** 