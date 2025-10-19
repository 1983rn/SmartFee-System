#!/usr/bin/env python3
"""
Quick fix for income error - Add missing other_income_total
"""

def fix_income_error():
    """Fix the missing other_income_total variable"""
    
    # Read the app.py file
    with open('app.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find line 1520 (boarding_total calculation for current_school_id) and add other_income_total after it
    for i, line in enumerate(lines):
        if 'boarding_total = db.session.query(db.func.sum(Student.boarding_amount_paid)).filter_by(school_id=current_school_id).scalar() or 0' in line:
            # Insert other_income_total calculation after this line
            lines.insert(i + 1, '        other_income_total = db.session.query(db.func.sum(OtherIncome.amount_paid)).filter_by(school_id=current_school_id).scalar() or 0\n')
            break
    
    # Find line 1525 (boarding_total calculation for developer view) and add other_income_total after it
    for i, line in enumerate(lines):
        if 'boarding_total = db.session.query(db.func.sum(Student.boarding_amount_paid)).scalar() or 0' in line and 'Developer view' in lines[i-3]:
            # Insert other_income_total calculation after this line
            lines.insert(i + 1, '        other_income_total = db.session.query(db.func.sum(OtherIncome.amount_paid)).scalar() or 0\n')
            break
    
    # Find line 1570 (boarding_total=boarding_total,) and add other_income_total after it
    for i, line in enumerate(lines):
        if 'boarding_total=boarding_total,' in line:
            # Insert other_income_total parameter after this line
            lines.insert(i + 1, '        other_income_total=other_income_total,\n')
            break
    
    # Write back to file
    with open('app.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("✅ Fixed income error - added other_income_total calculation and parameter")

if __name__ == '__main__':
    print("🔧 Applying quick fix for income error...")
    fix_income_error()
    print("✅ Fix applied! The 'other_income_total' undefined error should be resolved.")
    print("\nYou can now restart your Flask application and the income page should work correctly.")