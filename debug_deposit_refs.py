#!/usr/bin/env python3
"""
Debug script to check deposit slip references in the database
"""
import os
import sys
from datetime import datetime

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Income, Receipt

def check_deposit_references():
    with app.app_context():
        print("=== CHECKING DEPOSIT SLIP REFERENCES ===\n")
        
        # Check Income table
        print("1. INCOME TABLE:")
        income_records = Income.query.all()
        print(f"Total income records: {len(income_records)}")
        
        if income_records:
            print("\nSample income records:")
            for i, income in enumerate(income_records[:5]):  # Show first 5
                print(f"  ID: {income.id}")
                print(f"  Student: {income.student_name}")
                print(f"  Date: {income.payment_date}")
                print(f"  Reference: '{income.payment_reference}'")
                print(f"  Fee Type: {income.fee_type}")
                print("  ---")
        else:
            print("  No income records found!")
        
        # Check Receipt table
        print("\n2. RECEIPT TABLE:")
        receipt_records = Receipt.query.all()
        print(f"Total receipt records: {len(receipt_records)}")
        
        if receipt_records:
            print("\nSample receipt records:")
            for i, receipt in enumerate(receipt_records[:5]):  # Show first 5
                print(f"  ID: {receipt.id}")
                print(f"  Student: {receipt.student_name}")
                print(f"  Date: {receipt.payment_date}")
                print(f"  Deposit Slip Ref: '{receipt.deposit_slip_ref}'")
                print(f"  Fee Type: {receipt.fee_type}")
                print("  ---")
        else:
            print("  No receipt records found!")
        
        # Count records with missing references
        print("\n3. MISSING REFERENCES:")
        income_missing = Income.query.filter(
            (Income.payment_reference == None) | (Income.payment_reference == '')
        ).count()
        receipt_missing = Receipt.query.filter(
            (Receipt.deposit_slip_ref == None) | (Receipt.deposit_slip_ref == '')
        ).count()
        
        print(f"Income records with missing references: {income_missing}")
        print(f"Receipt records with missing references: {receipt_missing}")

if __name__ == "__main__":
    check_deposit_references()