#!/usr/bin/env python3
"""
Fix Income Error - Add missing other_income_total calculation
"""

import re
import os

def fix_income_route():
    """Fix the income route to include other_income_total calculation"""
    
    # Read the app.py file
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the income totals calculation section and add other_income_total
    # Look for the pattern where pta_total, sdf_total, boarding_total are calculated
    pattern1 = r'(# Calculate totals from actual student payments \(school-filtered\)\s+if current_school_id:\s+pta_total = db\.session\.query\(db\.func\.sum\(Student\.pta_amount_paid\)\)\.filter_by\(school_id=current_school_id\)\.scalar\(\) or 0\s+sdf_total = db\.session\.query\(db\.func\.sum\(Student\.sdf_amount_paid\)\)\.filter_by\(school_id=current_school_id\)\.scalar\(\) or 0\s+boarding_total = db\.session\.query\(db\.func\.sum\(Student\.boarding_amount_paid\)\)\.filter_by\(school_id=current_school_id\)\.scalar\(\) or 0)'
    
    replacement1 = r'''\1
        other_income_total = db.session.query(db.func.sum(OtherIncome.amount_paid)).filter_by(school_id=current_school_id).scalar() or 0'''
    
    content = re.sub(pattern1, replacement1, content, flags=re.MULTILINE | re.DOTALL)
    
    # Also fix the else clause (developer view)
    pattern2 = r'(else:\s+# Developer view - all schools\s+pta_total = db\.session\.query\(db\.func\.sum\(Student\.pta_amount_paid\)\)\.scalar\(\) or 0\s+sdf_total = db\.session\.query\(db\.func\.sum\(Student\.sdf_amount_paid\)\)\.scalar\(\) or 0\s+boarding_total = db\.session\.query\(db\.func\.sum\(Student\.boarding_amount_paid\)\)\.scalar\(\) or 0)'
    
    replacement2 = r'''\1
        other_income_total = db.session.query(db.func.sum(OtherIncome.amount_paid)).scalar() or 0'''
    
    content = re.sub(pattern2, replacement2, content, flags=re.MULTILINE | re.DOTALL)
    
    # Find the render_template call and add other_income_total parameter
    pattern3 = r'(return render_template\(\s+\'income\.html\',\s+grouped_incomes=grouped_incomes,\s+pta_total=pta_total,\s+sdf_total=sdf_total,\s+boarding_total=boarding_total,)\s+(other_incomes=other_incomes,)'
    
    replacement3 = r'''\1
        other_income_total=other_income_total,
        \2'''
    
    content = re.sub(pattern3, replacement3, content, flags=re.MULTILINE | re.DOTALL)
    
    # If the above pattern doesn't match, try a simpler approach
    if 'other_income_total=other_income_total,' not in content:
        # Find the render_template call and add the parameter
        pattern4 = r'(render_template\(\s+\'income\.html\',\s+grouped_incomes=grouped_incomes,\s+pta_total=pta_total,\s+sdf_total=sdf_total,\s+boarding_total=boarding_total,)\s+(other_incomes=other_incomes,)'
        
        replacement4 = r'''\1
        other_income_total=other_income_total,
        \2'''
        
        content = re.sub(pattern4, replacement4, content, flags=re.MULTILINE | re.DOTALL)
    
    # Write back to file
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Fixed income route - added other_income_total calculation and parameter")

def main():
    """Apply the fix"""
    print("🔧 Fixing Income Error...")
    print("=" * 40)
    
    try:
        # Check if app.py exists
        if not os.path.exists('app.py'):
            print("❌ Error: app.py file not found!")
            return
        
        # Apply the fix
        fix_income_route()
        
        print("=" * 40)
        print("✅ Income error fixed successfully!")
        print("\n📋 Changes made:")
        print("1. ✅ Added other_income_total calculation in income route")
        print("2. ✅ Added other_income_total parameter to render_template call")
        print("\n🎯 The 'other_income_total' is undefined error should now be resolved!")
        
    except Exception as e:
        print(f"❌ Error applying fix: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()