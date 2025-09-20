"""
Minimal SMS service for tenant enforcement system
"""

class SMSService:
    """Minimal SMS service class for compatibility"""
    
    def send_payment_confirmation(self, student, phone, payment_details):
        """Mock SMS sending"""
        return {'success': True, 'message': 'SMS would be sent in production'}
    
    def send_bulk_reminders(self, students):
        """Mock bulk SMS sending"""
        return [{'success': True, 'student_id': s['student'].student_id} for s in students]
    
    def send_balance_reminder(self, student, phone):
        """Mock balance reminder SMS"""
        return {'success': True, 'message': 'Balance reminder would be sent in production'}
    
    def send_sms(self, phone, message):
        """Mock SMS sending"""
        return {'success': True, 'message': 'SMS would be sent in production'}

# Create instance
sms_service = SMSService()