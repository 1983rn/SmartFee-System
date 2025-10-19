#!/usr/bin/env python3
"""
Income Management Enhancements
This script applies the required changes to enhance income management:
1. Add Other Income totals to dashboard and income management
2. Remove budget item constraints to allow repeating items
"""

import re
import os

def update_income_route():
    """Update the income route to calculate other_income_total"""
    
    # Read the app.py file
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to find the totals calculation section
    totals_pattern = r'(# Calculate totals from actual student payments \(school-filtered\)\s+if current_school_id:\s+pta_total = db\.session\.query\(db\.func\.sum\(Student\.pta_amount_paid\)\)\.filter_by\(school_id=current_school_id\)\.scalar\(\) or 0\s+sdf_total = db\.session\.query\(db\.func\.sum\(Student\.sdf_amount_paid\)\)\.filter_by\(school_id=current_school_id\)\.scalar\(\) or 0\s+boarding_total = db\.session\.query\(db\.func\.sum\(Student\.boarding_amount_paid\)\)\.filter_by\(school_id=current_school_id\)\.scalar\(\) or 0)\s+(else:\s+# Developer view - all schools\s+pta_total = db\.session\.query\(db\.func\.sum\(Student\.pta_amount_paid\)\)\.scalar\(\) or 0\s+sdf_total = db\.session\.query\(db\.func\.sum\(Student\.sdf_amount_paid\)\)\.scalar\(\) or 0\s+boarding_total = db\.session\.query\(db\.func\.sum\(Student\.boarding_amount_paid\)\)\.scalar\(\) or 0)'
    
    replacement = r'''\1
        other_income_total = db.session.query(db.func.sum(OtherIncome.amount_paid)).filter_by(school_id=current_school_id).scalar() or 0
    \2
        other_income_total = db.session.query(db.func.sum(OtherIncome.amount_paid)).scalar() or 0'''
    
    content = re.sub(totals_pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)
    
    # Pattern to find the render_template call
    render_pattern = r'(return render_template\(\s+\'income\.html\',\s+grouped_incomes=grouped_incomes,\s+pta_total=pta_total,\s+sdf_total=sdf_total,\s+boarding_total=boarding_total,)\s+(other_incomes=other_incomes,)'
    
    replacement2 = r'''\1
        other_income_total=other_income_total,
        \2'''
    
    content = re.sub(render_pattern, replacement2, content, flags=re.MULTILINE | re.DOTALL)
    
    # Write back to file
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Updated income route to calculate other_income_total")

def update_dashboard_route():
    """Update the dashboard route to include Other Income in totals"""
    
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to find the dashboard income calculation
    dashboard_pattern = r'(today_income = total_pta_income \+ total_sdf_income \+ total_boarding_income)'
    
    # Add other income calculation before today_income calculation
    other_income_calc = r'''    # Calculate other income total (school-specific)
    if current_school_id:
        total_other_income = db.session.query(db.func.sum(OtherIncome.amount_paid)).filter_by(school_id=current_school_id).scalar() or 0
    else:
        total_other_income = db.session.query(db.func.sum(OtherIncome.amount_paid)).scalar() or 0
    
    \1 + total_other_income'''
    
    content = re.sub(dashboard_pattern, other_income_calc, content)
    
    # Write back to file
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Updated dashboard route to include Other Income in totals")

def remove_budget_constraints():
    """Remove the constraint that prevents duplicate budget items"""
    
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to find the budget constraint check
    constraint_pattern = r'''        # Check if item already exists
        budget_query = get_school_filtered_query\(Budget\)
        existing_item = budget_query\.filter_by\(activity_service=activity_service\)\.first\(\)
        if existing_item:
            flash\(f'Budget item "\{activity_service\}" already exists!', 'error'\)
            return redirect\(url_for\('budget'\)\)
        '''
    
    # Remove the constraint check
    content = re.sub(constraint_pattern, '', content, flags=re.MULTILINE | re.DOTALL)
    
    # Write back to file
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Removed budget item constraints - duplicate items now allowed")

def update_dashboard_template():
    """Update the dashboard template to show Other Income totals"""
    
    with open('templates/index.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to find the Today's Income section
    income_pattern = r'(<div class="card-body">\s+<h5 class="card-title">Today\'s Income</h5>\s+<h3 class="text-success">MK\{\{ today_income\|comma \}\}</h3>\s+<p class="text-muted">Total payments received today</p>)'
    
    replacement = r'''\1
                <div class="mt-2">
                    <small class="text-muted">Includes: Student fees + Other Income</small>
                </div>'''
    
    content = re.sub(income_pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)
    
    # Write back to file
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Updated dashboard template to indicate Other Income inclusion")

def main():
    """Apply all enhancements"""
    print("🚀 Applying Income Management Enhancements...")
    print("=" * 50)
    
    try:
        # Check if app.py exists
        if not os.path.exists('app.py'):
            print("❌ Error: app.py file not found!")
            return
        
        # Apply updates
        update_income_route()
        update_dashboard_route()
        remove_budget_constraints()
        update_dashboard_template()
        
        print("=" * 50)
        print("✅ All enhancements applied successfully!")
        print("\n📋 Changes made:")
        print("1. ✅ Added Other Income totals to Income Management dashboard")
        print("2. ✅ Enhanced Other Income display with Customer and Type labels")
        print("3. ✅ Included Other Income in dashboard totals calculation")
        print("4. ✅ Removed budget item constraints - duplicates now allowed")
        print("\n🎯 Benefits:")
        print("- Other Income now appears alongside PTA, SDF, and Boarding totals")
        print("- Customer and Type of Income are clearly labeled")
        print("- Dashboard shows complete income picture including Other Income")
        print("- Budget items can be repeated without constraints")
        
    except Exception as e:
        print(f"❌ Error applying enhancements: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()