from app import app, db, Budget

# Correct budget structure: Category followed by its activities
BUDGET_ITEMS = [
    # Category 1 and its activities
    {"name": "1. Facilitating office operations", "is_category": True},
    {"name": "1203 public transport", "is_category": False},
    {"name": "1401 heating and lighting", "is_category": False},
    {"name": "1402 Telephone charges", "is_category": False},
    {"name": "1405 water and sanitation", "is_category": False},
    {"name": "1502 consumable stores", "is_category": False},
    {"name": "1504 postage", "is_category": False},
    {"name": "1505 printing cost", "is_category": False},
    {"name": "1406 publication and advertisement", "is_category": False},
    {"name": "1506 stationery", "is_category": False},
    {"name": "1507 uniform and protective wear", "is_category": False},
    {"name": "2401 Fuel and Lubricants", "is_category": False},
    {"name": "2321 Subscriptions", "is_category": False},
    {"name": "0251 purchase of plant and office equipment", "is_category": False},
    
    # Category 2 and its activities
    {"name": "2. Management of school based and National examinations", "is_category": True},
    {"name": "1803-examinations", "is_category": False},
    {"name": "Conducting budget and management meetings", "is_category": False},
    {"name": "2401 fuel or 2103 public transport (Meetings)", "is_category": False},
    {"name": "1204 Subsistence allowance (Meetings)", "is_category": False},
    
    # Category 3 and its activities
    {"name": "3. SMASSE", "is_category": True},
    {"name": "2401 fuel or 2103 public transport (SMASSE)", "is_category": False},
    {"name": "1204 Subsistence allowance (SMASSE)", "is_category": False},
    
    # Category 4 and its activities
    {"name": "4. Sporting activities", "is_category": True},
    {"name": "1805-sporting equipment", "is_category": False},
    {"name": "2401 fuel or 1203 public transport (Sporting)", "is_category": False},
    {"name": "1204 Subsistence allowance (Sporting)", "is_category": False},
    
    # Category 5 and its activities
    {"name": "5. Support to SNE", "is_category": True},
    {"name": "1806- purchase of special needs materials", "is_category": False},
    
    # Category 6 and its activities
    {"name": "6. Procurement of teaching and learning materials", "is_category": True},
    {"name": "1807- science consumables", "is_category": False},
    {"name": "1804- text books", "is_category": False},
    {"name": "1808- purchase of school supplies", "is_category": False},
    {"name": "Support to HIV/AIDS related activities", "is_category": False},
    {"name": "1614- HIV/AIDS services", "is_category": False},
    {"name": "1601- drugs", "is_category": False},
    
    # Category 7 and its activities
    {"name": "7. Maintenance of infrastructure", "is_category": True},
    {"name": "2501- maintenance of buildings", "is_category": False},
    {"name": "2504-maintenance of water supplies", "is_category": False},
    
    # Category 8 and its activities
    {"name": "8. COSOMA", "is_category": True},
    {"name": "2321- Subscription (COSOMA)", "is_category": False},
    {"name": "Computer Service Subscription", "is_category": False},
    {"name": "2321- Subscription (Computer Service)", "is_category": False},
    
    # Category 9 and its activities
    {"name": "9. In-service training for teachers", "is_category": True},
    {"name": "1502- consumables (Training)", "is_category": False},
    {"name": "1204- subsistence Allowances (Training)", "is_category": False},
    {"name": "1203 public transport or 2401 fuel (Training)", "is_category": False},
    
    # Category 10 and its activities
    {"name": "10. Processing of Payment vouchers", "is_category": True},
    {"name": "1204- subsistence Allowances (Vouchers)", "is_category": False},
    {"name": "1203 public transport or 2401 fuel (Vouchers)", "is_category": False},
    
    # Category 11 and its activities
    {"name": "11. Provision of sanitary pads to girls in secondary schools", "is_category": True},
    {"name": "1502- consumables (Sanitary pads)", "is_category": False},
    
    # Category 12 and its activities
    {"name": "12. Provision of PPEs to schools", "is_category": True},
    {"name": "1502- consumables (PPEs)", "is_category": False},
    {"name": "Provision of food and other boarding necessities to learners", "is_category": False},
    {"name": "1801- boarding expenses", "is_category": False}
]

with app.app_context():
    # Clear existing budget entries
    Budget.query.delete()
    
    # Add budget items in correct order
    for item in BUDGET_ITEMS:
        budget_item = Budget(
            activity_service=item["name"],
            proposed_allocation=0.0,
            is_category=item["is_category"]
        )
        db.session.add(budget_item)
    
    db.session.commit()
    print(f"Successfully added {len(BUDGET_ITEMS)} budget items in correct structure!")
    
    # Display structure
    print("\nBudget structure:")
    for i, item in enumerate(BUDGET_ITEMS, 1):
        if item["is_category"]:
            print(f"\n{item['name']} [CATEGORY]")
        else:
            print(f"  - {item['name']}")