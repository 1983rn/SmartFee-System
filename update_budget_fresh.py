from app import app, db, Budget

# Fresh budget activities list
FRESH_BUDGET_ACTIVITIES = [
    "Facilitating office operations",
    "1203 public transport",
    "1401 heating and lighting",
    "1402 Telephone charges",
    "1405 water and sanitation",
    "1502 consumable stores",
    "1504 postage",
    "1505 printing cost",
    "1406 publication and advertisement",
    "1506 stationery",
    "1507 uniform and protective wear",
    "2401 Fuel and Lubricants",
    "2321 Subscriptions",
    "0251 purchase of plant and office equipment",
    "Management of school based and National examinations",
    "1803-examinations",
    "Conducting budget and management meetings",
    "2401 fuel or 2103 public transport",
    "1204 Subsistence allowance",
    "SMASSE",
    "2401 fuel or 2103 public transport (SMASSE)",
    "1204 Subsistence allowance (SMASSE)",
    "Sporting activities",
    "1805-sporting equipment",
    "2401 fuel or 1203 public transport (Sporting)",
    "1204 Subsistence allowance (Sporting)",
    "Support to SNE",
    "1806- purchase of special needs materials",
    "Procurement of teaching and learning materials",
    "1807- science consumables",
    "1804- text books",
    "1808- purchase of school supplies",
    "Support to HIV/AIDS related activities",
    "1614- HIV/AIDS services",
    "1601- drugs",
    "Maintenance of infrastructure",
    "2501- maintenance of buildings",
    "2504-maintenance of water supplies",
    "COSOMA",
    "2321- Subscription (COSOMA)",
    "Computer Service Subscription",
    "2321- Subscription (Computer Service)",
    "In-service training for teachers",
    "1502- consumables (Training)",
    "1204- subsistence Allowances (Training)",
    "1203 public transport or 2401 fuel (Training)",
    "Processing of Payment vouchers",
    "1204- subsistence Allowances (Vouchers)",
    "1203 public transport or 2401 fuel (Vouchers)",
    "Provision of sanitary pads to girls in secondary schools",
    "1502- consumables (Sanitary pads)",
    "Provision of PPEs to schools",
    "1502- consumables (PPEs)",
    "Provision of food and other boarding necessities to learners",
    "1801- boarding expenses"
]

with app.app_context():
    # Delete all existing budget entries
    Budget.query.delete()
    print("Cleared all existing budget entries.")
    
    # Add fresh activities
    for activity in FRESH_BUDGET_ACTIVITIES:
        budget_item = Budget(
            activity_service=activity,
            proposed_allocation=0.0
        )
        db.session.add(budget_item)
    
    db.session.commit()
    print(f"Successfully added {len(FRESH_BUDGET_ACTIVITIES)} fresh budget activities!")
    
    # Display added activities
    print("\nFresh budget activities:")
    for i, activity in enumerate(FRESH_BUDGET_ACTIVITIES, 1):
        print(f"{i:2d}. {activity}")