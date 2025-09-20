from app import app, db, Budget

# Exact budget list as provided
BUDGET_ITEMS = [
    # Category A
    {"name": "(A). Facilitating office operations", "is_category": True},
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
    
    # Category B
    {"name": "(B). Management of school based and National examinations", "is_category": True},
    {"name": "1803-examinations", "is_category": False},
    {"name": "Conducting budget and management meetings", "is_category": False},
    {"name": "2401 fuel 0r 2103 public transport (B)", "is_category": False},
    {"name": "1204 Subsistence allowance (B)", "is_category": False},
    
    # Category C
    {"name": "(C). SMASSE", "is_category": True},
    {"name": "2401 fuel 0r 2103 public transport (C)", "is_category": False},
    {"name": "1204 Subsistence allowance (C)", "is_category": False},
    
    # Category D
    {"name": "(D). Sporting activities", "is_category": True},
    {"name": "1805-sporting equipment", "is_category": False},
    {"name": "2401 fuel 0r 1203 public transport (D)", "is_category": False},
    {"name": "1204 Subsistence allowance (D)", "is_category": False},
    
    # Category E
    {"name": "(E). Support to SNE", "is_category": True},
    {"name": "1806- purchase of special needs materials", "is_category": False},
    
    # Category F
    {"name": "(F). Procurement of teaching and learning materials", "is_category": True},
    {"name": "1807- science consumables", "is_category": False},
    {"name": "1804- text books", "is_category": False},
    {"name": "1808- purchase of school supplies", "is_category": False},
    {"name": "Support to HIV/AIDS related activities", "is_category": False},
    {"name": "1614- HIV/AIDS services", "is_category": False},
    {"name": "1601- drugs", "is_category": False},
    
    # Category G
    {"name": "(G). Maintenance of infrastructure", "is_category": True},
    {"name": "2501- maintenance of buildings", "is_category": False},
    {"name": "2504-maintenance of water supplies", "is_category": False},
    
    # Category H
    {"name": "(H). COSOMA", "is_category": True},
    {"name": "2321- Subscription (H1)", "is_category": False},
    {"name": "Computer Service Subscription", "is_category": False},
    {"name": "2321- Subscription (H2)", "is_category": False},
    
    # Category I
    {"name": "(I). In-service training for teachers", "is_category": True},
    {"name": "1502- consumables (I)", "is_category": False},
    {"name": "1204- subsistence Allowances (I)", "is_category": False},
    {"name": "1203 public transport or 2401 fuel (I)", "is_category": False},
    
    # Category J
    {"name": "(J). Processing of Payment vouchers", "is_category": True},
    {"name": "1204- subsistence Allowances (J)", "is_category": False},
    {"name": "1203 public transport or 2401 fuel (J)", "is_category": False},
    
    # Category K
    {"name": "(K). Provision of sanitary pads to girls in secondary schools", "is_category": True},
    {"name": "1502- consumables (K)", "is_category": False},
    
    # Category L
    {"name": "(L). Provision of PPEs to schools", "is_category": True},
    {"name": "1502- consumables (L)", "is_category": False},
    
    # Category M
    {"name": "(M). Provision of food and other boarding necessities to learners", "is_category": True},
    {"name": "1801- boarding expenses", "is_category": False}
]

with app.app_context():
    # Add budget items exactly as provided
    for item in BUDGET_ITEMS:
        budget_item = Budget(
            activity_service=item["name"],
            proposed_allocation=0.0,
            is_category=item["is_category"]
        )
        db.session.add(budget_item)
    
    db.session.commit()
    print(f"Successfully added {len(BUDGET_ITEMS)} budget items exactly as provided!")
    
    # Display structure
    print("\nBudget structure:")
    for item in BUDGET_ITEMS:
        if item["is_category"]:
            print(f"\n{item['name']}")
        else:
            print(f"  - {item['name']}")