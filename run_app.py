#!/usr/bin/env python3
"""
Simple script to run the SmartFee application
"""

try:
    from app import app, db
    
    print("Starting SmartFee Revenue Collection System...")
    
    # Create database tables
    with app.app_context():
        db.create_all()
        print("Database tables created successfully")
    
    print("\n" + "="*60)
    print("SMARTFEE REVENUE COLLECTION SYSTEM")
    print("="*60)
    print("Access your system at: http://localhost:5001")
    print("Developer Login: CWED / RNTECH")
    print("="*60 + "\n")
    
    # Run the application
    app.run(host='127.0.0.1', port=5001, debug=True)
    
except ImportError as e:
    print(f"Import Error: {e}")
    print("Please install required packages: pip install flask flask-sqlalchemy flask-wtf python-dotenv")
    
except Exception as e:
    print(f"Error starting application: {e}")
    import traceback
    traceback.print_exc()