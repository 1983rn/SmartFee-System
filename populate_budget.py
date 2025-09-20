from app import app, db, Budget

# Predefined budget activities/services
BUDGET_ACTIVITIES = [
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
    "Conducting budget and management meetings - Transport",
    "Conducting budget and management meetings - Subsistence",
    "SMASSE - Transport",
    "SMASSE - Subsistence",
    "Sporting activities",
    "1805-sporting equipment",
    "Sporting activities - Transport",
    "Sporting activities - Subsistence",
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
    "Computer Service Subscription",
    "In-service training for teachers - Consumables",
    "In-service training for teachers - Subsistence",
    "In-service training for teachers - Transport",
    "Processing of Payment vouchers - Subsistence",
    "Processing of Payment vouchers - Transport",
    "Provision of sanitary pads to girls in secondary schools",
    "Provision of PPEs to schools",
    "Provision of food and other boarding necessities to learners"
]

with app.app_context():
    # Clear existing budget entries
    Budget.query.delete()
    
    # Add predefined activities
    added_count = 0
    for activity in BUDGET_ACTIVITIES:
        # Check if activity already exists
        existing = Budget.query.filter_by(activity_service=activity).first()
        if not existing:
            budget_item = Budget(
                activity_service=activity,
                proposed_allocation=0.0
            )
            db.session.add(budget_item)
            added_count += 1
    
    db.session.commit()
    print(f"Successfully added {added_count} budget activities!")
    
    # Display added activities
    print("\nAdded activities:")
    for i, activity in enumerate(BUDGET_ACTIVITIES, 1):
        print(f"{i:2d}. {activity}")