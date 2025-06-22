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
    
    def run_calendar_events_example(self):
        """Example: Calendar Events Integration"""
        print("\n📅 Calendar Events Example")
        print("=" * 35)
        
        # Get all calendar events
        calendar_events = list(self.fs.db.collection('calendar_events').stream())
        
        # Get upcoming events (next 7 days)
        today = datetime.now().strftime("%Y-%m-%d")
        week_ahead = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        upcoming_events = list(
            self.fs.db.collection('calendar_events')
            .where("date", ">=", today)
            .where("date", "<=", week_ahead)
            .order_by("date")
            .stream()
        )
        
        print(f"📊 Calendar Events Summary:")
        print(f"   Total events: {len(calendar_events)}")
        print(f"   Upcoming (7 days): {len(upcoming_events)}")
        
        if upcoming_events:
            print("   Upcoming events:")
            for event_doc in upcoming_events[:3]:
                event = event_doc.to_dict()
                print(f"     • {event.get('date')} at {event.get('time')}: {event.get('action', 'N/A')[:50]}...")
        
        return {'total': len(calendar_events), 'upcoming': len(upcoming_events)}
    
    def run_finance_events_example(self):
        """Example: Finance Events Integration"""
        print("\n💳 Finance Events Example")
        print("=" * 30)
        
        # Get all finance events
        finance_events = list(self.fs.db.collection('finance_events').stream())
        
        total_expenses = 0
        total_income = 0
        categories = {}
        
        print(f"📊 Finance Events Summary:")
        print(f"   Total events: {len(finance_events)}")
        
        for event_doc in finance_events:
            event = event_doc.to_dict()
            amount = float(event.get('amount', '0'))
            event_type = event.get('type', 'Unknown')
            category = event.get('category', 'Other')
            
            if event_type == 'Expense':
                total_expenses += amount
            elif event_type == 'Income':
                total_income += amount
            
            # Count by category
            if category not in categories:
                categories[category] = 0
            categories[category] += amount
        
        print(f"   Total expenses: €{total_expenses:,.2f}")
        print(f"   Total income: €{total_income:,.2f}")
        print(f"   Net: €{total_income - total_expenses:,.2f}")
        
        if categories:
            print("   Top categories:")
            sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
            for category, amount in sorted_categories[:3]:
                print(f"     • {category}: €{amount:,.2f}")
        
        return {
            'total_events': len(finance_events),
            'total_expenses': total_expenses,
            'total_income': total_income,
            'categories': len(categories)
        }
    
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
        self.run_calendar_events_example()
        self.run_finance_events_example()
        
        print("\n🎉 All examples completed!")

if __name__ == "__main__":
    examples = IntegrationExamples()
    examples.run_all_examples()
