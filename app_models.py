# Database Models
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school_configuration.id'), nullable=False)  # Link to school
    student_id = db.Column(db.String(50), nullable=False)  # Encrypted, increased size
    name = db.Column(db.String(200), nullable=False)  # Encrypted, increased size
    sex = db.Column(db.String(20), nullable=False)  # Encrypted
    form_class = db.Column(db.String(50), nullable=False)  # Encrypted
    parent_phone = db.Column(db.String(200))  # Encrypted phone number
    pta_amount_paid = db.Column(db.Float, default=0.0)
    sdf_amount_paid = db.Column(db.Float, default=0.0)
    boarding_amount_paid = db.Column(db.Float, default=0.0)
    pta_required = db.Column(db.Float, default=0.0)
    sdf_required = db.Column(db.Float, default=0.0)
    boarding_required = db.Column(db.Float, default=0.0)
    pta_installments = db.Column(db.Integer, default=0)  # Track number of PTA installments
    sdf_installments = db.Column(db.Integer, default=0)  # Track number of SDF installments
    boarding_installments = db.Column(db.Integer, default=0)  # Track number of Boarding installments
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to school
    school = db.relationship('SchoolConfiguration', backref='students')
    
    # Unique constraint to prevent duplicate student IDs within the same school
    __table_args__ = (db.UniqueConstraint('school_id', 'student_id', name='unique_school_student_id'),)
    
    def get_decrypted_student_id(self):
        """Get student ID (no decryption)"""
        return self.student_id
    
    def get_decrypted_name(self):
        """Get student name (no decryption)"""
        return self.name
    
    def get_decrypted_sex(self):
        """Get sex (no decryption)"""
        return self.sex
    
    def get_decrypted_form_class(self):
        """Get form class (no decryption)"""
        return self.form_class
    
    def get_decrypted_parent_phone(self):
        """Get parent phone (no decryption)"""
        return self.parent_phone
    
    def set_encrypted_data(self, student_id, name, sex, form_class, parent_phone=None):
        """Set student data (no encryption)"""
        # Store raw values directly
        self.student_id = student_id
        self.name = name
        self.sex = sex
        self.form_class = form_class
        self.parent_phone = parent_phone
    
    def is_paid_in_full(self):
        """Check if student has paid in full based on active fund configuration"""
        # Get active config for this school only
        active_config = FundConfiguration.query.filter_by(
            school_id=self.school_id, is_active=True
        ).first()
        if active_config:
            return (self.pta_amount_paid >= active_config.pta_amount and 
                   self.sdf_amount_paid >= active_config.sdf_amount and
                   self.boarding_amount_paid >= active_config.boarding_amount)
        return (self.pta_amount_paid >= self.pta_required and 
               self.sdf_amount_paid >= self.sdf_required and
               self.boarding_amount_paid >= self.boarding_required)
    
    def get_pta_balance(self):
        """Get PTA balance based on active fund configuration"""
        active_config = FundConfiguration.query.filter_by(
            school_id=self.school_id, is_active=True
        ).first()
        required = active_config.pta_amount if active_config else self.pta_required
        return max(0, required - self.pta_amount_paid)
    
    def get_sdf_balance(self):
        """Get SDF balance based on active fund configuration"""
        active_config = FundConfiguration.query.filter_by(
            school_id=self.school_id, is_active=True
        ).first()
        required = active_config.sdf_amount if active_config else self.sdf_required
        return max(0, required - self.sdf_amount_paid)
    
    def get_boarding_balance(self):
        """Get Boarding balance based on active fund configuration"""
        active_config = FundConfiguration.query.filter_by(
            school_id=self.school_id, is_active=True
        ).first()
        required = active_config.boarding_amount if active_config else self.boarding_required
        return max(0, required - self.boarding_amount_paid)
    
    def can_pay_installment(self, fee_type):
        """Check if student can pay another installment (max 2)"""
        if fee_type == 'PTA':
            return self.pta_installments < 2
        elif fee_type == 'SDF':
            return self.sdf_installments < 2
        elif fee_type == 'Boarding':
            return self.boarding_installments < 2
        return False

class Income(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school_configuration.id'), nullable=False)  # Link to school
    student_id = db.Column(db.String(50), nullable=False)  # Encrypted
    student_name = db.Column(db.String(200), nullable=False)  # Encrypted
    form_class = db.Column(db.String(50), nullable=False)  # Encrypted
    payment_date = db.Column(db.Date, nullable=False)
    payment_reference = db.Column(db.String(100), nullable=False)  # Encrypted
    fee_type = db.Column(db.String(20), nullable=False)  # Encrypted
    amount_paid = db.Column(db.Float, nullable=False)
    balance = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to school
    school = db.relationship('SchoolConfiguration', backref='incomes')

class Expenditure(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school_configuration.id'), nullable=False)  # Link to school
    date = db.Column(db.Date, nullable=False)
    activity_service = db.Column(db.String(400), nullable=False)  # Encrypted
    voucher_no = db.Column(db.String(100))  # Encrypted
    cheque_no = db.Column(db.String(100))  # Encrypted
    amount_paid = db.Column(db.Float, nullable=False)
    fund_type = db.Column(db.String(30), nullable=False)  # Encrypted
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to school
    school = db.relationship('SchoolConfiguration', backref='expenditures')

class FundConfiguration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school_configuration.id'), nullable=False)  # Link to school
    term_name = db.Column(db.String(100), nullable=False)  # Encrypted
    pta_amount = db.Column(db.Float, nullable=False, default=0.0)  # Allow 0.0 for schools without PTA
    sdf_amount = db.Column(db.Float, nullable=False, default=0.0)  # Allow 0.0 for schools without SDF
    boarding_amount = db.Column(db.Float, nullable=False, default=0.0)  # Allow 0.0 for schools without boarding
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to school
    school = db.relationship('SchoolConfiguration', backref='fund_configurations')

class SchoolConfiguration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_name = db.Column(db.String(200), nullable=False, default='School Name')
    school_address = db.Column(db.String(500), nullable=True)
    head_teacher_contact = db.Column(db.String(100), nullable=True)
    bursar_contact = db.Column(db.String(100), nullable=True)
    school_email = db.Column(db.String(100), nullable=True)
    encryption_key = db.Column(db.Text, nullable=True)  # Unique encryption key for this school
    is_active = db.Column(db.Boolean, default=True)
    is_blocked = db.Column(db.Boolean, default=False)
    subscription_status = db.Column(db.String(20), default='trial')  # trial, active, expired, blocked
    trial_start_date = db.Column(db.DateTime, default=datetime.utcnow)
    subscription_end_date = db.Column(db.DateTime, nullable=True)
    subscription_type = db.Column(db.String(20), default='trial')  # trial, 90days, 12months, 24months, absolute
    last_notification_sent = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Generate encryption key when school is created
        if not self.encryption_key:
            self.encryption_key = school_encryption.generate_school_key(self.id or 0)
    
    def get_encryption_key(self):
        """Get or generate encryption key for this school"""
        if not self.encryption_key:
            self.encryption_key = school_encryption.generate_school_key(self.id)
            db.session.commit()
        return self.encryption_key
    
    def days_remaining(self):
        """Calculate days remaining in subscription"""
        if self.subscription_status == 'trial':
            if self.trial_start_date:
                trial_end = self.trial_start_date + timedelta(days=30)
                remaining = (trial_end - datetime.utcnow()).days
                return max(0, remaining)
            else:
                # If no trial start date, assume trial just started
                self.trial_start_date = datetime.utcnow()
                db.session.commit()
                return 30
        elif self.subscription_end_date:
            remaining = (self.subscription_end_date - datetime.utcnow()).days
            return max(0, remaining)
        return 0
    
    def is_subscription_expired(self):
        """Check if subscription has expired"""
        return self.days_remaining() <= 0 and self.subscription_status != 'absolute'
    
    def needs_notification(self):
        """Check if school needs subscription reminder notification"""
        try:
            days_left = self.days_remaining()
            if days_left <= 7 and days_left > 0:  # Notify when 7 days or less remaining
                if not self.last_notification_sent:
                    return True
                # Send notification once per day
                last_notification = self.last_notification_sent.date() if self.last_notification_sent else None
                return last_notification != datetime.utcnow().date()
            return False
        except Exception:
            return False

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='school_admin')  # 'developer' or 'school_admin'
    school_id = db.Column(db.Integer, db.ForeignKey('school_configuration.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    first_login = db.Column(db.Boolean, default=True)
    is_one_time_password = db.Column(db.Boolean, default=True)  # True for one-time passwords set by developer
    password_change_required = db.Column(db.Boolean, default=True)  # Force password change on first login
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school_configuration.id'), nullable=False)
    subscription_type = db.Column(db.String(20), nullable=False)  # trial, 90days, 12months, 24months, absolute
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=True)
    amount_paid = db.Column(db.Float, default=0.0)
    payment_reference = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.String(50), nullable=False)  # Developer who created/updated
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def days_remaining(self):
        """Calculate days remaining in this subscription period"""
        if self.subscription_type == 'absolute':
            return float('inf')  # Unlimited
        if self.end_date:
            remaining = (self.end_date - datetime.utcnow()).days
            return max(0, remaining)
        return 0

class NotificationLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school_configuration.id'), nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)  # subscription_reminder, subscription_expired, etc.
    message = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    days_remaining = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Receipt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school_configuration.id'), nullable=False)  # Link to school
    receipt_no = db.Column(db.String(20), nullable=False)  # Encrypted
    student_id = db.Column(db.String(50), nullable=False)  # Encrypted
    student_name = db.Column(db.String(200), nullable=False)  # Encrypted
    form_class = db.Column(db.String(50), nullable=False)  # Encrypted
    payment_date = db.Column(db.Date, nullable=False)
    deposit_slip_ref = db.Column(db.String(100), nullable=False)  # Encrypted
    fee_type = db.Column(db.String(20), nullable=False)  # Encrypted
    amount_paid = db.Column(db.Float, nullable=False)
    balance = db.Column(db.Float, nullable=False)
    installment_number = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to school
    school = db.relationship('SchoolConfiguration', backref='receipts')
    
    @staticmethod
    def generate_receipt_number(school_id=None):
        """Generate next receipt number in payment order (0001 for first payment, etc.) - school-specific"""
        # Get the highest receipt number already used (as integer) for current school
        if school_id:
            last_receipt = Receipt.query.filter_by(school_id=school_id).order_by(Receipt.id.desc()).first()
        else:
            # Fallback for developer mode
            last_receipt = Receipt.query.order_by(Receipt.id.desc()).first()
        
        if last_receipt and last_receipt.receipt_no.isdigit():
            next_number = int(last_receipt.receipt_no) + 1
        else:
            next_number = 1
        return f"{next_number:04d}"

# Other Income Model
class OtherIncome(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school_configuration.id'), nullable=False)  # Link to school
    date = db.Column(db.Date, nullable=False)
    customer_name = db.Column(db.String(200), nullable=False)  # Encrypted
    income_type = db.Column(db.String(100), nullable=False)  # Encrypted
    total_charge = db.Column(db.Float, nullable=False)
    amount_paid = db.Column(db.Float, nullable=False)
    balance = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to school
    school = db.relationship('SchoolConfiguration', backref='other_incomes')

    @staticmethod
    def generate_receipt_number(school_id=None):
        """Generate receipt number for other income - school-specific"""
        if school_id:
            count = OtherIncome.query.filter_by(school_id=school_id).count()
        else:
            count = OtherIncome.query.count()
        return f"GR{count + 1:04d}"

# Budget Model
class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school_configuration.id'), nullable=False)  # Link to school
    activity_service = db.Column(db.String(400), nullable=False)  # Encrypted
    proposed_allocation = db.Column(db.Float, default=0.0)
    is_category = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to school
    school = db.relationship('SchoolConfiguration', backref='budgets')
    
    __table_args__ = (db.UniqueConstraint('school_id', 'activity_service', name='unique_school_activity'),)

# Professional Receipt Model
class ProfessionalReceipt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school_configuration.id'), nullable=False)
    receipt_no = db.Column(db.String(10), nullable=False)
    student_id = db.Column(db.String(50), nullable=False)
    pta_amount = db.Column(db.Float, default=0.0)
    sdf_amount = db.Column(db.Float, default=0.0)
    boarding_amount = db.Column(db.Float, default=0.0)
    reference_number = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to school
    school = db.relationship('SchoolConfiguration', backref='professional_receipts')
    
    # Unique constraint to prevent duplicate receipts for same student
    __table_args__ = (db.UniqueConstraint('school_id', 'student_id', name='unique_school_student_receipt'),)