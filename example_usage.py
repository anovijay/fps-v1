#!/usr/bin/env python3
"""
FPS (Email Processing Service) - Example Usage
Demonstrates how to use the batch processor and query structured file data
"""

import os
import sys
from typing import List, Dict, Any
from datetime import datetime

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from batch_processor import BatchProcessor
from firestore_service import FirestoreService
from config import Config

def example_basic_batch_processing():
    """
    Example 1: Basic batch processing (existing functionality)
    """
    print("🚀 Example 1: Basic Email Batch Processing")
    print("=" * 50)
    
    try:
        # Initialize the batch processor
        processor = BatchProcessor()
        
        # Process a batch of emails
        success = processor.process_batch()
        
        if success:
            print("✅ Batch processing completed successfully!")
        else:
            print("❌ Batch processing failed!")
            
    except Exception as e:
        print(f"❌ Error in batch processing: {e}")

def example_query_unpaid_invoices():
    """
    Example 2: Query unpaid invoices for expense tracking service
    """
    print("\n💰 Example 2: Query Unpaid Invoices for Expense Tracking")
    print("=" * 60)
    
    try:
        firestore_service = FirestoreService()
        
        # Get all unpaid invoices
        unpaid_invoices = firestore_service.get_unpaid_invoices(limit=10)
        
        print(f"📋 Found {len(unpaid_invoices)} unpaid invoices:")
        
        for invoice in unpaid_invoices:
            print(f"\n🧾 Invoice from {invoice.get('sender', 'Unknown')}")
            print(f"   Amount: {invoice.get('amount', 'N/A')}")
            print(f"   Due Date: {invoice.get('payment_due_date', 'N/A')}")
            print(f"   Status: {invoice.get('payment_status', 'Unknown')}")
            print(f"   Urgency: {invoice.get('urgency', 'N/A')}")
            print(f"   Action Required: {invoice.get('action_required', 'N/A')}")
            
        if not unpaid_invoices:
            print("✅ No unpaid invoices found!")
            
    except Exception as e:
        print(f"❌ Error querying unpaid invoices: {e}")

def example_monthly_expenses():
    """
    Example 3: Get monthly expenses for expense reporting
    """
    print("\n📊 Example 3: Monthly Expenses for Expense Reporting")
    print("=" * 55)
    
    try:
        firestore_service = FirestoreService()
        
        # Get current month expenses
        current_date = datetime.now()
        monthly_expenses = firestore_service.get_monthly_expenses(
            year=current_date.year, 
            month=current_date.month
        )
        
        print(f"📅 Expenses for {current_date.strftime('%B %Y')}:")
        print(f"📋 Found {len(monthly_expenses)} expense items:")
        
        total_amount = 0
        for expense in monthly_expenses:
            print(f"\n🧾 {expense.get('document_type', 'Document')} from {expense.get('sender', 'Unknown')}")
            print(f"   Date: {expense.get('received_date', 'N/A')}")
            print(f"   Amount: {expense.get('amount', 'N/A')}")
            print(f"   Status: {expense.get('payment_status', 'Unknown')}")
            print(f"   Tags: {', '.join(expense.get('tags', []))}")
            
            # Try to extract numeric amount for total (basic parsing)
            amount_str = expense.get('amount', '')
            if amount_str and any(char.isdigit() for char in amount_str):
                try:
                    # Basic amount extraction (this could be enhanced)
                    import re
                    numbers = re.findall(r'[\d,]+\.?\d*', amount_str)
                    if numbers:
                        amount_value = float(numbers[0].replace(',', ''))
                        total_amount += amount_value
                except:
                    pass
        
        print(f"\n💰 Estimated total: €{total_amount:,.2f}")
        
        if not monthly_expenses:
            print("✅ No expenses found for this month!")
            
    except Exception as e:
        print(f"❌ Error querying monthly expenses: {e}")

def example_urgent_items_briefing():
    """
    Example 4: Get urgent items for daily briefing service
    """
    print("\n🚨 Example 4: Urgent Items for Daily Briefing")
    print("=" * 50)
    
    try:
        firestore_service = FirestoreService()
        
        # Get urgent items
        urgent_items = firestore_service.get_urgent_items_for_briefing(
            urgency_levels=["High", "Critical"]
        )
        
        print(f"⚡ Found {len(urgent_items)} urgent items:")
        
        for item in urgent_items:
            urgency_emoji = "🔥" if item.get('urgency') == "Critical" else "⚠️"
            print(f"\n{urgency_emoji} {item.get('urgency', 'Unknown')} - {item.get('document_type', 'Document')}")
            print(f"   From: {item.get('sender', 'Unknown')}")
            print(f"   Date: {item.get('received_date', 'N/A')}")
            print(f"   Summary: {item.get('summary', 'N/A')}")
            print(f"   Action Required: {item.get('action_required', 'N/A')}")
            
            # Show payment info if it's an invoice
            if item.get('is_invoice') and item.get('payment_due_date'):
                print(f"   💰 Payment Due: {item.get('payment_due_date')}")
                print(f"   💳 Amount: {item.get('amount', 'N/A')}")
        
        if not urgent_items:
            print("✅ No urgent items found!")
            
    except Exception as e:
        print(f"❌ Error querying urgent items: {e}")

def example_payment_due_soon():
    """
    Example 5: Get payments due soon for reminder service
    """
    print("\n⏰ Example 5: Payments Due Soon (Next 7 Days)")
    print("=" * 50)
    
    try:
        firestore_service = FirestoreService()
        
        # Get payments due in the next 7 days
        due_soon = firestore_service.get_payment_due_soon(days_ahead=7)
        
        print(f"📅 Found {len(due_soon)} payments due soon:")
        
        for payment in due_soon:
            print(f"\n💳 Payment to {payment.get('sender', 'Unknown')}")
            print(f"   Amount: {payment.get('amount', 'N/A')}")
            print(f"   Due Date: {payment.get('payment_due_date', 'N/A')}")
            print(f"   Reference: {payment.get('payment_reference', 'N/A')}")
            print(f"   Method: {payment.get('payment_method', 'N/A')}")
            print(f"   Urgency: {payment.get('urgency', 'N/A')}")
        
        if not due_soon:
            print("✅ No payments due in the next 7 days!")
            
    except Exception as e:
        print(f"❌ Error querying payments due soon: {e}")

def example_documents_by_type():
    """
    Example 6: Get documents by type for categorization service
    """
    print("\n📄 Example 6: Documents by Type")
    print("=" * 35)
    
    try:
        firestore_service = FirestoreService()
        
        # Get different types of documents
        document_types = ["Invoice", "Receipt", "Contract"]
        
        for doc_type in document_types:
            documents = firestore_service.get_documents_by_type(doc_type, limit=5)
            print(f"\n📋 {doc_type}s found: {len(documents)}")
            
            for doc in documents:
                print(f"   • {doc.get('sender', 'Unknown')} - {doc.get('received_date', 'N/A')}")
                if doc.get('amount'):
                    print(f"     Amount: {doc.get('amount')}")
            
    except Exception as e:
        print(f"❌ Error querying documents by type: {e}")

def main():
    """
    Main function to run all examples
    
    NOTE: These examples are commented out to prevent accidental execution.
    Uncomment the ones you want to test.
    """
    print("🧪 FPS Email Processing Service - Usage Examples")
    print("=" * 60)
    print("⚠️  NOTE: Examples are commented out to prevent accidental execution")
    print("   Uncomment the examples you want to test before running this script")
    print("")
    
    # Uncomment the examples you want to test:
    
    # Example 1: Basic batch processing (processes real emails)
    # example_basic_batch_processing()
    
    # Example 2: Query unpaid invoices (safe to run)
    example_query_unpaid_invoices()
    
    # Example 3: Monthly expenses (safe to run)
    example_monthly_expenses()
    
    # Example 4: Urgent items for briefing (safe to run)
    example_urgent_items_briefing()
    
    # Example 5: Payments due soon (safe to run)
    example_payment_due_soon()
    
    # Example 6: Documents by type (safe to run)
    example_documents_by_type()
    
    print("\n✅ Examples completed!")
    print("\n💡 Integration Tips:")
    print("   • Use these query methods in your expense tracking service")
    print("   • Use urgent_items for daily briefing automation")
    print("   • Use monthly_expenses for automated expense reports")
    print("   • Use payment_due_soon for payment reminder notifications")

if __name__ == "__main__":
    main() 