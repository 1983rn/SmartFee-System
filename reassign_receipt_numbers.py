from app import db, Receipt

def reassign_receipt_numbers():
    # Get all receipts ordered by payment_date, then by id for tie-breaker
    receipts = Receipt.query.order_by(Receipt.payment_date, Receipt.id).all()
    for idx, receipt in enumerate(receipts, start=1):
        receipt.receipt_no = f"{idx:04d}"
    db.session.commit()
    print(f"Reassigned receipt numbers for {len(receipts)} receipts.")

if __name__ == "__main__":
    reassign_receipt_numbers()
