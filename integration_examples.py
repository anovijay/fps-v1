#!/usr/bin/env python3
"""
FPS Integration Examples - Comprehensive examples for other services
"""

import os
import sys
from datetime import datetime, timedelta

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from firestore_service import FirestoreService
except ImportError:
    print("❌ Error: Cannot import FirestoreService")
    sys.exit(1)

class IntegrationExamples:
    def __init__(self):
        self.fs = FirestoreService()
    
    def run_expense_tracking_example(self):
        """Example: Monthly Expense Tracking"""
        print("\n💰 Monthly Expense Tracking Example")
        print("=" * 40)
        
        current_date = datetime.now()
        expenses = self.fs.get_monthly_expenses(current_date.year, current_date.month)
        
        total_amount = 0
        unpaid_count = 0
        
        print(f"📅 Expenses for {current_date.year}-{current_date.month:02d}:")
        print(f"   Total items: {len(expenses)}")
        
        for expense in expenses:
            amount_str = expense.get('amount', '0')
            if '€' in amount_str:
                amount = float(amount_str.replace('€', '').replace(',', ''))
                total_amount += amount
            
            if expense.get('payment_status') == 'Unpaid':
                unpaid_count += 1
        
        print(f"   Total amount: €{total_amount:,.2f}")
        print(f"   Unpaid invoices: {unpaid_count}")
        
        return {'total': total_amount, 'unpaid': unpaid_count}
    
    def run_daily_briefing_example(self):
        """Example: Daily Briefing Service"""
        print("\n📰 Daily Briefing Example")
        print("=" * 30)
        
        urgent_items = self.fs.get_urgent_items_for_briefing()
        payments_due = self.fs.get_payment_due_soon(days_ahead=7)
        
        print(f"📋 Today's briefing:")
        print(f"   🚨 Urgent items: {len(urgent_items)}")
        print(f"   💰 Payments due soon: {len(payments_due)}")
        
        if urgent_items:
            print("   Urgent items:")
            for item in urgent_items[:3]:
                print(f"     • {item.get('document_type')} from {item.get('sender')}")
        
        return {'urgent': len(urgent_items), 'due_soon': len(payments_due)}
    
    def run_all_examples(self):
        """Run all examples"""
        print("🧪 FPS Integration Examples")
        print("=" * 50)
        
        # Test connection
        if not self.fs.test_connection():
            print("❌ Cannot connect to Firestore")
            return
        
        print("✅ Connected to Firestore")
        
        # Run examples
        self.run_expense_tracking_example()
        self.run_daily_briefing_example()
        
        print("\n🎉 Examples completed!")

if __name__ == "__main__":
    examples = IntegrationExamples()
    examples.run_all_examples()
