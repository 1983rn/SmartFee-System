from app import app, db, Budget

with app.app_context():
    # Delete all budget entries
    Budget.query.delete()
    db.session.commit()
    print("All budget entries have been cleared. Ready for fresh list.")