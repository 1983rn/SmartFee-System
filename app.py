from datetime import datetime as dt
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect, generate_csrf
from datetime import datetime, timedelta
from functools import wraps
from security import init_security
import os
from dotenv import load_dotenv
from jinja2 import ChoiceLoader, FileSystemLoader, DictLoader
from sms_service import sms_service
from encryption_utils import school_encryption, encrypt_sensitive_field, decrypt_sensitive_field, encrypt_phone_field, decrypt_phone_field
from data_isolation_helpers import get_current_school_id, ensure_school_access, get_school_filtered_query, decrypt_student_data

# Load environment variables from .env file
load_dotenv()

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'),
    static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'),
)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Set up instance path for SQLite and other app data
instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
if not os.path.exists(instance_path):
    os.makedirs(instance_path)
app.instance_path = instance_path

# Initialize security features
init_security(app)

# Set secure session configuration
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PREFERRED_URL_SCHEME'] = 'https'

# Configure a fallback Jinja loader so /login doesn't 500 if template missing in deployment
try:
        if app.template_folder and os.path.isdir(app.template_folder):
                file_loader = FileSystemLoader(app.template_folder)
        else:
                file_loader = FileSystemLoader('templates')

        # Minimal in-memory fallback templates to avoid 500s when templates are missing
        fallback_login_html = """
        <!DOCTYPE html>
        <html><head><meta charset="utf-8"><title>Login</title>
        <meta name="viewport" content="width=device-width, initial-scale=1"></head>
        <body style="font-family:Arial, sans-serif; max-width:480px; margin:40px auto;">
            <h2>SmartFee Login</h2>
            <p style="color:#c00">Note: Using fallback in-memory template because templates/login.html was not found on server.</p>
            {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div>{{ message }}</div>
                {% endfor %}
            {% endif %}
            {% endwith %}
            <form method="POST">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}" />
                <div><label>Username</label><br><input name="username" required></div>
                <div><label>Password</label><br><input type="password" name="password" required></div>
                <input type="hidden" name="login_type" value="school">
                <button type="submit">Login</button>
            </form>
        </body></html>
        """

        fallback_base_html = """
        <!doctype html>
        <html>
            <head>
                <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
                <title>{{ school_name or 'SmartFee' }}</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            </head>
            <body class="container py-4">
                <header class="mb-4"><h3>{{ school_name or 'SmartFee Revenue Collection System' }}</h3></header>
                <main>
                    {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="alert alert-{{ 'danger' if category == 'error' else category }}">{{ message }}</div>
                        {% endfor %}
                    {% endif %}
                    {% endwith %}
                    {% block content %}{% endblock %}
                </main>
            </body>
        </html>
        """

        fallback_index_html = """
        {% extends 'base.html' %}
        {% block content %}
            <div class="card"><div class="card-body">
                <h5 class="card-title">Welcome to SmartFee</h5>
                <p class="card-text">The templates directory was not found on the server. Showing fallback page.</p>
                <a class="btn btn-primary" href="{{ url_for('login') }}">Go to Login</a>
            </div></div>
        {% endblock %}
        """

        # Set up Jinja loader via jinja_env to combine filesystem and in-memory fallbacks
        app.jinja_env.loader = ChoiceLoader([file_loader, DictLoader({
            'login.html': fallback_login_html,
            'base.html': fallback_base_html,
            'index.html': fallback_index_html
        })])
except Exception as e:
        print(f"Startup check warning (templates path): {e}")

# Database configuration
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
    # Use PostgreSQL on Render, correcting the scheme for SQLAlchemy
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url.replace("postgres://", "postgresql://", 1)
else:
    # Use SQLite for local development, placing the DB in the 'instance' folder
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(instance_path, 'smartfee.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
csrf = CSRFProtect(app)

# Ensure csrf_token() is available in Jinja templates
@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf)

# Health check endpoint for external monitoring and Netlify proxy test
@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'service': 'smartfee-backend',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })

# Serve favicon if present, otherwise return 204 to avoid log spam
@app.route('/favicon.ico')
def favicon():
    try:
        static_folder = app.static_folder or 'static'
        icon_path = os.path.join(static_folder, 'favicon.ico')
        if app.static_folder and os.path.exists(icon_path):
            return send_from_directory(app.static_folder, 'favicon.ico', mimetype='image/x-icon')
    except Exception as e:
        # Fall through to 204 if any error
        print(f"favicon warning: {e}")
    return ('', 204)

# Diagnostic route to verify templates path in production
@app.route('/templates_check')
def templates_check():
    try:
        templates_dir = app.template_folder or 'templates'
        login_template_path = os.path.join(templates_dir, 'login.html')
        exists = os.path.exists(login_template_path)
        listing = []
        if os.path.isdir(templates_dir):
            try:
                listing = sorted(os.listdir(templates_dir))
            except Exception as e:
                listing = [f"error listing dir: {e}"]
        return jsonify({
            'templates_dir': templates_dir,
            'login_exists': exists,
            'dir_listing': listing
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Tenant schema helpers (PostgreSQL only)
from sqlalchemy import text

def is_postgres() -> bool:
    uri = app.config.get('SQLALCHEMY_DATABASE_URI', '') or ''
    return uri.startswith('postgresql://')

def get_tenant_schema_name(school_id: int) -> str:
    return f"school_{school_id}"

def create_tenant_schema_and_tables(school_id: int):
    """Create per-tenant schema and tenant tables if using PostgreSQL.
    Keeps global tables (SchoolConfiguration, User, Subscription, NotificationLog) in public.
    """
    if not is_postgres():
        return
    schema = get_tenant_schema_name(school_id)
    # Create schema and tables within that schema using a dedicated connection
    with db.engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        # Switch search_path to tenant schema for table creation
        conn.execute(text(f"SET search_path TO {schema}"))
        # Create tenant tables only, checkfirst avoids overwriting
        try:
            Student.__table__.create(bind=conn, checkfirst=True)
            Income.__table__.create(bind=conn, checkfirst=True)
            Expenditure.__table__.create(bind=conn, checkfirst=True)
            FundConfiguration.__table__.create(bind=conn, checkfirst=True)
            Receipt.__table__.create(bind=conn, checkfirst=True)
            OtherIncome.__table__.create(bind=conn, checkfirst=True)
            Budget.__table__.create(bind=conn, checkfirst=True)
            ProfessionalReceipt.__table__.create(bind=conn, checkfirst=True)
        except Exception as e:
            # Log and continue; tables may already exist
            print(f"Tenant table creation warning for {schema}: {e}")

@app.before_request
def apply_tenant_search_path():
    """Set search_path per request and validate tenant access."""
    # Skip validation for login/logout routes
    if request.endpoint in ['login', 'logout', 'static']:
        return
    
    try:
        if is_postgres():
            role = session.get('user_role')
            school_id = session.get('school_id')
            
            if role != 'developer' and school_id:
                # Enhanced tenant validation
                school = SchoolConfiguration.query.get(school_id)
                if not school or not school.is_active or school.is_blocked:
                    if 'logged_in' in session:
                        session.clear()
                        flash('School access revoked. Please contact support.', 'error')
                    return redirect(url_for('login'))
                
                # Check subscription status
                if school.subscription_status == 'expired' and school.days_remaining() <= 0:
                    if 'logged_in' in session:
                        session.clear()
                        flash('Subscription expired. Please contact support.', 'error')
                    return redirect(url_for('login'))
                
                # Set tenant schema
                schema = get_tenant_schema_name(school_id)
                db.session.execute(text(f"SET search_path TO {schema}, public"))
            else:
                # Default to public for developer
                db.session.execute(text("SET search_path TO public"))
                
    except Exception as e:
        # Do not break request if search_path fails
        print(f"apply_tenant_search_path warning: {e}")

# Default credentials (loaded from environment variables for security)
DEFAULT_USERNAME = os.environ.get('DEFAULT_USERNAME', 'CWED')
DEFAULT_PASSWORD = os.environ.get('DEFAULT_PASSWORD', 'RNTECH')

# Multi-tenant access validator
def validate_tenant_access():
    """Validate current user's tenant access"""
    if session.get('user_role') == 'developer':
        return True
    
    school_id = session.get('school_id')
    if not school_id:
        return False
    
    school = SchoolConfiguration.query.get(school_id)
    if not school or not school.is_active or school.is_blocked:
        return False
    
    # Check subscription status
    if school.subscription_status == 'expired' and school.days_remaining() <= 0:
        return False
    
    return True

# Authentication decorator with enhanced multi-tenancy
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        
        # Enhanced multi-tenancy validation
        if not validate_tenant_access():
            session.clear()
            flash('Access denied or subscription expired. Please contact support.', 'error')
            return redirect(url_for('login'))
        
        return f(*args, **kwargs)
    return decorated_function

# All route decorators and functions are now after app and login_required are defined
@app.route('/print_professional_receipt/<student_id>')
@login_required
def print_professional_receipt(student_id):
    current_school_id = get_current_school_id()
    if not current_school_id and session.get('user_role') != 'developer':
        flash('No school access configured. Please contact administrator.', 'error')
        return redirect(url_for('index'))

    # Get school-filtered students and find by student_id
    student_query = get_school_filtered_query(Student)
    students = student_query.all()
    student = None
    for s in students:
        if s.student_id == student_id:
            student = s
            break
    
    if not student:
        flash('Student not found!', 'error')
        return redirect(url_for('income'))
    
    # Check if student has paid in full
    if not student.is_paid_in_full():
        flash('Receipt can only be generated for students who have paid in full!', 'error')
        return redirect(url_for('income'))
    
    # Check if receipt already exists for this student
    existing_receipt = ProfessionalReceipt.query.filter_by(
        school_id=current_school_id, 
        student_id=student.student_id
    ).first()
    
    if existing_receipt:
        # Use existing receipt
        receipt_no = existing_receipt.receipt_no
        deposit_ref = existing_receipt.reference_number
    else:
        # Generate new receipt number
        existing_receipts = ProfessionalReceipt.query.filter_by(school_id=current_school_id).count()
        receipt_no = f"{existing_receipts + 1:03d}"
        
        # Get reference number from latest income record
        income_query = get_school_filtered_query(Income)
        latest_income = income_query.filter_by(student_id=student.student_id).order_by(Income.payment_date.desc()).first()
        deposit_ref = None
        if latest_income and latest_income.payment_reference:
            if latest_income.school and latest_income.school.encryption_key:
                deposit_ref = decrypt_sensitive_field(latest_income.payment_reference, latest_income.school_id, latest_income.school.encryption_key)
            else:
                deposit_ref = latest_income.payment_reference
        
        # Create professional receipt record
        professional_receipt = ProfessionalReceipt(
            school_id=current_school_id,
            receipt_no=receipt_no,
            student_id=student.student_id,
            pta_amount=student.pta_amount_paid,
            sdf_amount=student.sdf_amount_paid,
            boarding_amount=student.boarding_amount_paid,
            reference_number=deposit_ref
        )
        db.session.add(professional_receipt)
        db.session.commit()
    
    # Get school configuration
    school_config = SchoolConfiguration.query.filter_by(id=current_school_id, is_active=True).first()
    school_name = school_config.school_name if school_config else 'School Name'
    school_address = school_config.school_address if school_config and school_config.school_address else None
    
    # Get active fund configuration
    fund_config_query = get_school_filtered_query(FundConfiguration)
    active_config = fund_config_query.filter_by(is_active=True).first()
    term_name = active_config.term_name if active_config else 'Current Term'
    
    # Decrypt student data for display
    decrypted_data = decrypt_student_data(student)
    
    return render_template(
        'professional_receipt.html',
        school_name=school_name,
        school_address=school_address,
        receipt_no=receipt_no,
        student_id=decrypted_data['student_id'],
        student_name=decrypted_data['name'],
        form_class=decrypted_data['form_class'],
        term=term_name,
        date=dt.now().strftime('%Y-%m-%d'),
        deposit_ref=deposit_ref or 'N/A',
        pta_amount=student.pta_amount_paid,
        sdf_amount=student.sdf_amount_paid,
        boarding_amount=student.boarding_amount_paid,
        total_amount=student.pta_amount_paid + student.sdf_amount_paid + student.boarding_amount_paid
    )

# Note: 4-up receipts feature removed. Individual professional receipt printing remains available via /print_professional_receipt/<student_id>.

# Helper functions
def generate_student_id():
    """Generate the next sequential student ID"""
    current_school_id = get_current_school_id()
    if not current_school_id:
        return "0001"  # Fallback for developer mode
    
    # Get school-filtered students
    student_query = get_school_filtered_query(Student)
    students = student_query.all()
    
    if not students:
        return "0001"
    
    # Get all existing student ID numbers for this school
    existing_numbers = set()
    for student in students:
        try:
            # Since we're not using encryption, just use the student_id directly
            student_id = student.student_id
            
            # Try to extract number from student ID
            if student_id and student_id.isdigit():
                existing_numbers.add(int(student_id))
        except (ValueError, Exception):
            # If ID is not numeric, continue
            continue
    
    # Find the next sequential number
    if not existing_numbers:
        return "0001"
    
    next_number = max(existing_numbers) + 1
    return f"{next_number:04d}"  # Format as 4-digit number (0001, 0002, etc.)

# Custom Jinja2 filter for number formatting with commas
@app.template_filter('comma')
def comma_filter(value):
    """Format number with comma separators (2 decimal places)"""
    try:
        return "{:,.2f}".format(float(value))
    except (ValueError, TypeError):
        return value

@app.template_filter('comma_int')
def comma_int_filter(value):
    """Format number with comma separators (no decimal places)"""
    try:
        return "{:,}".format(int(float(value)))
    except (ValueError, TypeError):
        return value

# Make datetime and school name available in templates
@app.context_processor
def inject_globals():
    # Get school config for current user's school, but never fail template rendering
    try:
        current_school_id = get_current_school_id()
        if current_school_id:
            school_config = SchoolConfiguration.query.filter_by(
                id=current_school_id, is_active=True
            ).first()
        else:
            school_config = None
    except Exception as e:
        # Avoid breaking pages like /login if DB is not ready or tables missing
        print(f"inject_globals warning: {e}")
        school_config = None

    school_name = school_config.school_name if school_config else 'SmartFee Revenue Collection System'
    school_address = school_config.school_address if school_config and school_config.school_address else None
    software_name = 'SmartFee Revenue Collection System'
    return {
        'datetime': datetime,
        'school_name': school_name,
        'school_address': school_address,
        'software_name': software_name,
        'session': session,
    }

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    # If sensitive params accidentally appear in query string, strip them by redirecting to clean URL
    if request.method == 'GET' and request.args:
        # Avoid potential credential leakage in logs and history
        return redirect(url_for('login'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        login_type = request.form.get('login_type', 'school')
        
        # Developer login
        DEV_USERNAME = os.environ.get('DEV_USERNAME', 'CWED')
        DEV_PASSWORD = os.environ.get('DEV_PASSWORD', 'RNTECH')

        if login_type == 'developer':
            if DEV_USERNAME and username == DEV_USERNAME and password == DEV_PASSWORD:
                session['logged_in'] = True
                session['username'] = username
                session['user_role'] = 'developer'
                session['school_id'] = None
                flash('Developer login successful!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid developer credentials!', 'error')
        
        # School administrator login with enhanced multi-tenancy
        else:
            user = User.query.filter_by(username=username, password=password, is_active=True).first()
            if user:
                # Validate school access
                if user.school_id:
                    school = SchoolConfiguration.query.get(user.school_id)
                    if not school or not school.is_active:
                        flash('School account is inactive. Please contact support.', 'error')
                        return render_template('login.html')
                    if school.is_blocked:
                        flash('School account is suspended. Please contact support.', 'error')
                        return render_template('login.html')
                
                session['logged_in'] = True
                session['username'] = username
                session['user_role'] = user.role
                session['school_id'] = user.school_id
                
                # Check if first login setup is required
                if user.first_login or user.password_change_required:
                    return redirect(url_for('first_login_setup'))
                
                flash('Login successful!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password!', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully!', 'info')
    return redirect(url_for('login'))

@app.route('/first_login_setup', methods=['GET', 'POST'])
@login_required
def first_login_setup():
    if request.method == 'POST':
        new_username = request.form.get('new_username', '').strip()
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        if new_password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('first_login_setup.html')
        
        if len(new_password) < 6:
            flash('Password must be at least 6 characters long!', 'error')
            return render_template('first_login_setup.html')
        
        user = User.query.filter_by(username=session['username']).first()
        if user:
            # Update username if provided and different
            if new_username and new_username != user.username:
                # Check if new username already exists
                existing_user = User.query.filter_by(username=new_username).first()
                if existing_user:
                    flash('Username already exists! Please choose a different username.', 'error')
                    return render_template('first_login_setup.html')
                user.username = new_username
                session['username'] = new_username
            
            user.password = new_password
            user.first_login = False
            user.password_change_required = False
            user.is_one_time_password = False
            user.updated_at = datetime.utcnow()
            db.session.commit()
            flash('Credentials updated successfully!', 'success')
            return redirect(url_for('index'))
    
    user = User.query.filter_by(username=session['username']).first()
    return render_template('first_login_setup.html', user=user)

@app.route('/create_school_admin', methods=['GET', 'POST'])
@login_required
def create_school_admin():
    if session.get('user_role') != 'developer':
        flash('Access denied. Developer privileges required.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        school_name = request.form['school_name']
        
        try:
            # Check if username already exists
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash(f'Username "{username}" already exists! Please choose a different username.', 'error')
                return render_template('create_school_admin.html')
            
            # Create school configuration with trial subscription
            school_config = SchoolConfiguration(
                school_name=school_name,
                is_active=True,
                subscription_status='trial',
                subscription_type='trial',
                trial_start_date=datetime.utcnow()
            )
            db.session.add(school_config)
            db.session.flush()
            
            # Generate encryption key after getting school ID
            if not school_config.encryption_key:
                school_config.encryption_key = school_encryption.generate_school_key(school_config.id)
            
            # Create school admin user with one-time password
            user = User(
                username=username,
                password=password,
                role='school_admin',
                school_id=school_config.id,
                first_login=True,
                is_one_time_password=True,
                password_change_required=True
            )
            db.session.add(user)
            
            # Create initial trial subscription record
            trial_subscription = Subscription(
                school_id=school_config.id,
                subscription_type='trial',
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=30),
                amount_paid=0.0,
                created_by=session['username'],
                notes='Initial 30-day trial subscription'
            )
            db.session.add(trial_subscription)
            
            db.session.commit()
            
            flash(f'School administrator created for {school_name}! Username: {username} (One-time password - must be changed on first login)', 'success')
            return redirect(url_for('manage_schools'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating school administrator: {str(e)}', 'error')
    
    schools = SchoolConfiguration.query.order_by(SchoolConfiguration.created_at.desc()).all()
    return render_template('create_school_admin.html', schools=schools)

@app.route('/manage_schools')
@login_required
def manage_schools():
    if session.get('user_role') != 'developer':
        flash('Access denied. Developer privileges required.', 'error')
        return redirect(url_for('index'))
    
    # Get all schools with their users and subscription info
    schools_data = []
    schools = SchoolConfiguration.query.all()
    
    # First, fix any None subscription_status values and trial_start_date
    for school in schools:
        if school.subscription_status is None:
            school.subscription_status = 'trial'
        if school.subscription_type is None:
            school.subscription_type = 'trial'
        if school.trial_start_date is None:
            school.trial_start_date = datetime.utcnow()
    db.session.commit()
    
    for school in schools:
        # Get school admin user
        admin_user = User.query.filter_by(school_id=school.id, role='school_admin').first()
        
        # Get current subscription
        current_subscription = Subscription.query.filter_by(
            school_id=school.id, is_active=True
        ).order_by(Subscription.created_at.desc()).first()
        
        # Get notification logs
        recent_notifications = NotificationLog.query.filter_by(
            school_id=school.id
        ).order_by(NotificationLog.sent_at.desc()).limit(3).all()
        
        schools_data.append({
            'school': school,
            'admin_user': admin_user,
            'subscription': current_subscription,
            'notifications': recent_notifications,
            'days_remaining': school.days_remaining(),
            'needs_notification': school.needs_notification()
        })
    
    return render_template('manage_schools.html', schools_data=schools_data)

@app.route('/debug_session')
@login_required
def debug_session():
    """Debug route to check session data"""
    return jsonify(dict(session))

@app.route('/block_school/<int:school_id>', methods=['POST'])
@login_required
def block_school(school_id):
    if session.get('user_role') != 'developer':
        flash('Access denied. Developer privileges required.', 'error')
        return redirect(url_for('index'))
    
    school = SchoolConfiguration.query.get_or_404(school_id)
    school.is_blocked = True
    school.subscription_status = 'blocked'
    db.session.commit()
    flash(f'School "{school.school_name}" has been blocked!', 'success')
    return redirect(url_for('manage_schools'))

@app.route('/unblock_school/<int:school_id>', methods=['POST'])
@login_required
def unblock_school(school_id):
    if session.get('user_role') != 'developer':
        flash('Access denied. Developer privileges required.', 'error')
        return redirect(url_for('index'))
    
    school = SchoolConfiguration.query.get_or_404(school_id)
    school.is_blocked = False
    school.subscription_status = 'active'
    db.session.commit()
    flash(f'School "{school.school_name}" has been unblocked!', 'success')
    return redirect(url_for('manage_schools'))

@app.route('/delete_school/<int:school_id>', methods=['POST'])
@login_required
def delete_school(school_id):
    if session.get('user_role') != 'developer':
        flash('Access denied. Developer privileges required.', 'error')
        return redirect(url_for('manage_schools'))
    
    try:
        school = SchoolConfiguration.query.get_or_404(school_id)
        school_name = school.school_name
        
        # Use raw SQL to delete records to avoid foreign key update issues
        from sqlalchemy import text
        
        # Delete in correct order to handle foreign key constraints
        db.session.execute(text("DELETE FROM income WHERE school_id = :school_id"), {'school_id': school_id})
        db.session.execute(text("DELETE FROM receipt WHERE school_id = :school_id"), {'school_id': school_id})
        db.session.execute(text("DELETE FROM expenditure WHERE school_id = :school_id"), {'school_id': school_id})
        db.session.execute(text("DELETE FROM other_income WHERE school_id = :school_id"), {'school_id': school_id})
        db.session.execute(text("DELETE FROM budget WHERE school_id = :school_id"), {'school_id': school_id})
        db.session.execute(text("DELETE FROM fund_configuration WHERE school_id = :school_id"), {'school_id': school_id})
        db.session.execute(text("DELETE FROM student WHERE school_id = :school_id"), {'school_id': school_id})
        db.session.execute(text("DELETE FROM user WHERE school_id = :school_id"), {'school_id': school_id})
        db.session.execute(text("DELETE FROM subscription WHERE school_id = :school_id"), {'school_id': school_id})
        db.session.execute(text("DELETE FROM notification_log WHERE school_id = :school_id"), {'school_id': school_id})
        db.session.execute(text("DELETE FROM school_configuration WHERE id = :school_id"), {'school_id': school_id})
        
        db.session.commit()
        flash(f'School "{school_name}" and all associated data deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting school: {str(e)}', 'error')
    
    return redirect(url_for('manage_schools'))

@app.route('/update_subscription/<int:school_id>', methods=['POST'])
@login_required
def update_subscription(school_id):
    if session.get('user_role') != 'developer':
        flash('Access denied. Developer privileges required.', 'error')
        return redirect(url_for('manage_schools'))
    
    try:
        school = SchoolConfiguration.query.get_or_404(school_id)
        subscription_type = request.form['subscription_type']
        amount_paid = float(request.form.get('amount_paid', 0))
        payment_reference = request.form.get('payment_reference', '')
        notes = request.form.get('notes', '')
        
        # Deactivate current subscriptions
        Subscription.query.filter_by(school_id=school_id, is_active=True).update({'is_active': False})
        
        # Calculate end date based on subscription type
        start_date = datetime.utcnow()
        end_date = None
        
        if subscription_type == '90days':
            end_date = start_date + timedelta(days=90)
        elif subscription_type == '12months':
            end_date = start_date + timedelta(days=365)
        elif subscription_type == '24months':
            end_date = start_date + timedelta(days=730)
        elif subscription_type == 'absolute':
            end_date = None  # No expiration
        
        # Create new subscription
        new_subscription = Subscription(
            school_id=school_id,
            subscription_type=subscription_type,
            start_date=start_date,
            end_date=end_date,
            amount_paid=amount_paid,
            payment_reference=payment_reference,
            created_by=session['username'],
            notes=notes
        )
        db.session.add(new_subscription)
        
        # Update school configuration
        school.subscription_status = 'active' if subscription_type != 'trial' else 'trial'
        school.subscription_type = subscription_type
        school.subscription_end_date = end_date
        school.is_blocked = False
        school.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash(f'Subscription updated successfully for {school.school_name}!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating subscription: {str(e)}', 'error')
    
    return redirect(url_for('manage_schools'))

@app.route('/reset_school_credentials/<int:school_id>', methods=['POST'])
@login_required
def reset_school_credentials(school_id):
    if session.get('user_role') != 'developer':
        flash('Access denied. Developer privileges required.', 'error')
        return redirect(url_for('manage_schools'))
    
    try:
        school = SchoolConfiguration.query.get_or_404(school_id)
        admin_user = User.query.filter_by(school_id=school_id, role='school_admin').first()
        
        new_username = request.form['new_username']
        new_password = request.form['new_password']
        
        if admin_user:
            # Update existing user
            admin_user.username = new_username
            admin_user.password = new_password
            admin_user.is_one_time_password = True
            admin_user.password_change_required = True
            admin_user.first_login = True
            admin_user.updated_at = datetime.utcnow()
        else:
            # Create new admin user
            admin_user = User(
                username=new_username,
                password=new_password,
                role='school_admin',
                school_id=school_id,
                is_one_time_password=True,
                password_change_required=True,
                first_login=True
            )
            db.session.add(admin_user)
        
        db.session.commit()
        flash(f'Credentials reset successfully for {school.school_name}! Username: {new_username}', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error resetting credentials: {str(e)}', 'error')
    
    return redirect(url_for('manage_schools'))

@app.route('/send_notification/<int:school_id>', methods=['POST'])
@login_required
def send_notification(school_id):
    if session.get('user_role') != 'developer':
        flash('Access denied. Developer privileges required.', 'error')
        return redirect(url_for('manage_schools'))
    
    try:
        school = SchoolConfiguration.query.get_or_404(school_id)
        days_remaining = school.days_remaining()
        
        if days_remaining <= 0:
            message = f"Your subscription has expired. Please contact support to renew your subscription."
            notification_type = "subscription_expired"
        else:
            message = f"Your subscription will expire in {days_remaining} days. Please renew to avoid service interruption."
            notification_type = "subscription_reminder"
        
        # Log the notification
        notification = NotificationLog(
            school_id=school_id,
            notification_type=notification_type,
            message=message,
            days_remaining=days_remaining
        )
        db.session.add(notification)
        
        # Update last notification sent
        school.last_notification_sent = datetime.utcnow()
        
        db.session.commit()
        flash(f'Notification sent to {school.school_name}!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error sending notification: {str(e)}', 'error')
    
    return redirect(url_for('manage_schools'))

@app.route('/edit_other_income/<int:income_id>', methods=['GET', 'POST'])
@login_required
def edit_other_income(income_id):
    # Ensure other income belongs to current school
    other_income_query = get_school_filtered_query(OtherIncome)
    other_income = other_income_query.filter_by(id=income_id).first_or_404()
    income_types = ['House Rentals', 'Classroom Rentals', 'Chairs', 'Tables', 'Desks', 'Car hire', 'Others']
    
    if request.method == 'POST':
        try:
            other_income.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
            other_income.customer_name = request.form['customer_name']
            other_income.income_type = request.form['income_type']
            other_income.total_charge = float(request.form['total_charge'])
            other_income.amount_paid = float(request.form['amount_paid'])
            other_income.balance = other_income.total_charge - other_income.amount_paid
            
            db.session.commit()
            flash('Other income record updated successfully!', 'success')
            return redirect(url_for('income'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating other income: {str(e)}', 'error')
    
    return render_template('edit_other_income.html', other_income=other_income, income_types=income_types)

@app.route('/delete_other_income/<int:income_id>', methods=['POST'])
@login_required
def delete_other_income(income_id):
    try:
        # Ensure other income belongs to current school
        other_income_query = get_school_filtered_query(OtherIncome)
        other_income = other_income_query.filter_by(id=income_id).first_or_404()
        customer_name = other_income.customer_name
        db.session.delete(other_income)
        db.session.commit()
        flash(f'Other income record for "{customer_name}" deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting other income record: {str(e)}', 'error')
    return redirect(url_for('income'))

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
# Routes

# Helper function to ensure database schema is up to date
def ensure_database_schema():
    """Ensure all required database columns exist"""
    try:
        # Only applicable to SQLite local dev. Skip on Postgres (Render)
        if is_postgres():
            return
        # Check if the new school configuration columns exist
        from sqlalchemy import text
        
        # Get current columns
        result = db.session.execute(text("PRAGMA table_info(school_configuration)"))
        existing_columns = [row[1] for row in result.fetchall()]
        
        # Add missing columns
        required_columns = [
            ('school_address', 'TEXT'),
            ('head_teacher_contact', 'TEXT'),
            ('bursar_contact', 'TEXT'),
            ('school_email', 'TEXT')
        ]
        
        for column_name, column_type in required_columns:
            if column_name not in existing_columns:
                try:
                    db.session.execute(text(f"ALTER TABLE school_configuration ADD COLUMN {column_name} {column_type}"))
                    db.session.commit()
                    print(f"Added column: {column_name}")
                except Exception as e:
                    if "duplicate column" not in str(e).lower():
                        print(f"Error adding column {column_name}: {e}")
                    db.session.rollback()
        
    except Exception as e:
        print(f"Error ensuring database schema: {e}")
        db.session.rollback()

# Helper function to create default user on first run
def create_default_school_and_admin():
    """Creates a default school and an admin user if none exist."""
    # For Render deployment, these must be set as environment variables.
    # For local dev, they can be in the .env file.
    admin_username = os.environ.get('DEFAULT_USERNAME')
    admin_password = os.environ.get('DEFAULT_PASSWORD')

    if not admin_username or not admin_password:
        print("WARNING: DEFAULT_USERNAME and/or DEFAULT_PASSWORD are not set. Skipping default admin creation.")
        return

    # Check if any user exists
    if User.query.first() is None:
        print("INFO: No users found in the database. Creating default school and admin user...")
        
        # 1. Create a default school configuration
        default_school = SchoolConfiguration.query.filter_by(school_name='Default School').first()
        if not default_school:
            default_school = SchoolConfiguration(
                school_name='Default School',
                is_active=True,
                is_blocked=False,
                subscription_status='active'
            )
            db.session.add(default_school)
            db.session.flush()  # Flush to get the school's ID before committing

        # 2. Create a default admin user using credentials from environment or defaults
        admin_user = User(
            username=admin_username,
            password=admin_password,
            role='developer',
            school_id=None,
            is_active=True,
            first_login=False  # Default admin doesn't need to change password on first login
        )
        db.session.add(admin_user)
        db.session.commit()
        print(f"SUCCESS: Default admin '{admin_username}' created for 'Default School'.")
from sqlalchemy import desc

# Routes
@app.route('/')
@login_required
def index():
    current_school_id = get_current_school_id()
    
    # Developers should not see school data - redirect to manage schools
    if session.get('user_role') == 'developer':
        return redirect(url_for('manage_schools'))
    
    if not current_school_id:
        flash('No school access configured. Please contact administrator.', 'error')
        return redirect(url_for('logout'))
    
    # Get school-filtered queries
    student_query = get_school_filtered_query(Student)
    expenditure_query = get_school_filtered_query(Expenditure)
    fund_config_query = get_school_filtered_query(FundConfiguration)
    
    total_students = student_query.count()
    
    # Count students who are paid in full based on fund configuration
    all_students = student_query.all()
    paid_in_full = sum(1 for student in all_students if student.is_paid_in_full())
    outstanding_count = total_students - paid_in_full
    
    today = datetime.now().date()
    
    # Calculate total income from all student payments (school-specific)
    total_pta_income = db.session.query(db.func.sum(Student.pta_amount_paid)).filter_by(school_id=current_school_id).scalar() or 0
    total_sdf_income = db.session.query(db.func.sum(Student.sdf_amount_paid)).filter_by(school_id=current_school_id).scalar() or 0
    total_boarding_income = db.session.query(db.func.sum(Student.boarding_amount_paid)).filter_by(school_id=current_school_id).scalar() or 0
    total_other_income = db.session.query(db.func.sum(OtherIncome.amount_paid)).filter_by(school_id=current_school_id).scalar() or 0
    
    # Calculate total expenditure including all fund types (student fees + other income expenditures)
    total_expenditure = expenditure_query.with_entities(db.func.sum(Expenditure.amount_paid)).scalar() or 0
    
    today_income = total_pta_income + total_sdf_income + total_boarding_income + total_other_income
    
    # Get recent expenditures for display
    recent_expenditures = expenditure_query.order_by(Expenditure.date.desc()).limit(5).all()
    
    # Get active fund configuration for current school
    active_config = fund_config_query.filter_by(is_active=True).first()
    
    return render_template('index.html', 
                         total_students=total_students,
                         paid_in_full=paid_in_full,
                         outstanding_count=outstanding_count,
                         today_income=today_income,
                         total_expenditure=total_expenditure,
                         recent_expenditures=recent_expenditures,
                         active_config=active_config)

# Other Income routes
@app.route('/other_income', methods=['GET', 'POST'])
@login_required
def other_income():
    current_school_id = get_current_school_id()
    if not current_school_id and session.get('user_role') != 'developer':
        flash('No school access configured. Please contact administrator.', 'error')
        return redirect(url_for('index'))
    
    income_types = ['House Rentals', 'Classroom Rentals', 'Chairs', 'Tables', 'Desks', 'Car hire', 'Others']
    
    if request.method == 'POST':
        try:
            date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
            customer_name = request.form['customer_name']
            income_type = request.form['income_type']
            total_charge = float(request.form['total_charge'])
            amount_paid = float(request.form['amount_paid'])
            balance = total_charge - amount_paid
            
            other_income = OtherIncome(
                school_id=current_school_id,
                date=date,
                customer_name=customer_name,
                income_type=income_type,
                total_charge=total_charge,
                amount_paid=amount_paid,
                balance=balance
            )
            db.session.add(other_income)
            db.session.commit()
            flash('Other income recorded successfully!', 'success')
            return redirect(url_for('other_income'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error recording other income: {str(e)}', 'error')
    
    # Get other income records for display
    other_income_query = get_school_filtered_query(OtherIncome)
    other_incomes = other_income_query.order_by(OtherIncome.date.desc()).all()
    
    # Decrypt other income data for display
    for other_income in other_incomes:
        if other_income.school and other_income.school.encryption_key:
            other_income.decrypted_customer_name = decrypt_sensitive_field(other_income.customer_name, other_income.school_id, other_income.school.encryption_key)
            other_income.decrypted_income_type = decrypt_sensitive_field(other_income.income_type, other_income.school_id, other_income.school.encryption_key)
        else:
            other_income.decrypted_customer_name = other_income.customer_name
            other_income.decrypted_income_type = other_income.income_type
    
    return render_template('other_income.html', income_types=income_types, other_incomes=other_incomes)

@app.route('/add_other_income', methods=['GET', 'POST'])
@login_required
def add_other_income():
    income_types = ['House Rentals', 'Classroom Rentals', 'Chairs', 'Tables', 'Desks', 'Car hire', 'Others']
    
    if request.method == 'POST':
        try:
            date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
            customer_name = request.form['customer_name']
            income_type = request.form['income_type']
            total_charge = float(request.form['total_charge'])
            amount_paid = float(request.form['amount_paid'])
            balance = total_charge - amount_paid
            
            current_school_id = get_current_school_id()
            if not current_school_id:
                flash('No school access configured. Please contact administrator.', 'error')
                return render_template('add_other_income.html', income_types=income_types)
            
            other_income = OtherIncome(
                school_id=current_school_id,
                date=date,
                customer_name=customer_name,
                income_type=income_type,
                total_charge=total_charge,
                amount_paid=amount_paid,
                balance=balance
            )
            db.session.add(other_income)
            db.session.commit()
            flash('Other income recorded successfully!', 'success')
            return redirect(url_for('income'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error recording other income: {str(e)}', 'error')
    
    return render_template('add_other_income.html', income_types=income_types)

@app.route('/other_income_receipt/<int:income_id>')
@login_required
def other_income_receipt(income_id):
    # Ensure other income belongs to current school
    other_income_query = get_school_filtered_query(OtherIncome)
    other_income = other_income_query.filter_by(id=income_id).first_or_404()
    return render_template('other_income_receipt.html', other_income=other_income)

@app.route('/general_receipt/<int:other_income_id>')
@login_required
def general_receipt_other_income(other_income_id):
    # Ensure other income belongs to current school
    other_income_query = get_school_filtered_query(OtherIncome)
    other_income = other_income_query.filter_by(id=other_income_id).first_or_404()
    return render_template('other_income_receipt.html', other_income=other_income)

@app.route('/print_other_income_receipt/<int:income_id>')
@login_required
def print_other_income_receipt(income_id):
    # Ensure other income belongs to current school
    other_income_query = get_school_filtered_query(OtherIncome)
    other_income = other_income_query.filter_by(id=income_id).first_or_404()
    return render_template('print_other_income_receipt.html', other_income=other_income)

# Redirect old general receipt route to new professional receipt
@app.route('/general_receipt/<student_id>')
@login_required
def general_receipt(student_id):
    return redirect(url_for('print_professional_receipt', student_id=student_id))

@app.route('/professional_receipts')
@login_required
def professional_receipts():
    """Display all professional receipts for the current school"""
    # Developers should not see school data
    if session.get('user_role') == 'developer':
        flash('Access denied. Developers cannot view school data.', 'error')
        return redirect(url_for('manage_schools'))
    
    current_school_id = get_current_school_id()
    if not current_school_id:
        flash('No school access configured. Please contact administrator.', 'error')
        return redirect(url_for('index'))
    
    # Get all professional receipts for current school
    receipts = ProfessionalReceipt.query.filter_by(school_id=current_school_id).order_by(ProfessionalReceipt.created_at.desc()).all()
    
    # Get student information for each receipt
    receipt_data = []
    for receipt in receipts:
        # Find student by student_id
        student_query = get_school_filtered_query(Student)
        students = student_query.all()
        student = None
        for s in students:
            if s.student_id == receipt.student_id:
                student = s
                break
        
        if student:
            decrypted_data = decrypt_student_data(student)
            receipt_data.append({
                'receipt': receipt,
                'student_name': decrypted_data['name'],
                'student_id': decrypted_data['student_id'],
                'form_class': decrypted_data['form_class'],
                'total_amount': receipt.pta_amount + receipt.sdf_amount + receipt.boarding_amount
            })
    
    return render_template('professional_receipts_list.html', receipts=receipt_data)




@app.route('/students')
@login_required
def students():
    # Developers should not see school data
    if session.get('user_role') == 'developer':
        flash('Access denied. Developers cannot view school data.', 'error')
        return redirect(url_for('manage_schools'))
    
    search_query = request.args.get('search', '').strip()
    
    # Get school-filtered base query
    query = get_school_filtered_query(Student)
    
    # Apply search filter if provided (search on encrypted data won't work well)
    # For now, we'll get all students and filter in Python after decryption
    students = query.all()
    
    # Decrypt student data for display and apply search filter
    decrypted_students = []
    for student in students:
        decrypted_data = decrypt_student_data(student)
        if not search_query or search_query.lower() in decrypted_data['name'].lower():
            student.decrypted_student_id = decrypted_data['student_id']
            student.decrypted_name = decrypted_data['name']
            student.decrypted_sex = decrypted_data['sex']
            student.decrypted_form_class = decrypted_data['form_class']
            decrypted_students.append(student)
    
    students = decrypted_students
    
    # Sort students by student ID number (0001, 0002, 0003, etc.)
    students.sort(key=lambda x: int(x.decrypted_student_id) if x.decrypted_student_id.isdigit() else 9999)
    
    # Calculate statistics
    stats = {}
    total_girls = 0
    total_boys = 0
    
    for student in students:
        form_class = student.decrypted_form_class
        if form_class not in stats:
            stats[form_class] = {'girls': 0, 'boys': 0, 'total': 0}
        
        if student.decrypted_sex == 'Female':
            stats[form_class]['girls'] += 1
            total_girls += 1
        else:
            stats[form_class]['boys'] += 1
            total_boys += 1
        
        stats[form_class]['total'] += 1
    
    total_enrollment = total_girls + total_boys
    
    return render_template('students.html', 
                         students=students, 
                         search_query=search_query,
                         stats=stats,
                         total_girls=total_girls,
                         total_boys=total_boys,
                         total_enrollment=total_enrollment)


@app.route('/print_students_stats')
@login_required
def print_students_stats():
    """Render the student statistics as a printable page (opens in new tab)."""
    # Recompute statistics to ensure consistent data
    query = get_school_filtered_query(Student)
    students = query.all()

    decrypted_students = []
    for student in students:
        decrypted_data = decrypt_student_data(student)
        student.decrypted_student_id = decrypted_data['student_id']
        student.decrypted_name = decrypted_data['name']
        student.decrypted_sex = decrypted_data['sex']
        student.decrypted_form_class = decrypted_data['form_class']
        decrypted_students.append(student)

    students = decrypted_students

    # Calculate statistics
    stats = {}
    total_girls = 0
    total_boys = 0

    for student in students:
        form_class = student.decrypted_form_class
        if form_class not in stats:
            stats[form_class] = {'girls': 0, 'boys': 0, 'total': 0}
        if student.decrypted_sex == 'Female':
            stats[form_class]['girls'] += 1
            total_girls += 1
        else:
            stats[form_class]['boys'] += 1
            total_boys += 1
        stats[form_class]['total'] += 1

    total_enrollment = total_girls + total_boys

    school_name = None
    try:
        current_school_id = get_current_school_id()
        school = SchoolConfiguration.query.get(current_school_id) if current_school_id else None
        school_name = school.school_name if school else 'School'
    except Exception:
        school_name = 'School'

    return render_template('students_stats_print.html', stats=stats, total_girls=total_girls, total_boys=total_boys, total_enrollment=total_enrollment, school_name=school_name)

@app.route('/edit_student/<int:student_id>', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    # Ensure student belongs to current school
    student_query = get_school_filtered_query(Student)
    student = student_query.filter_by(id=student_id).first_or_404()
    
    if request.method == 'POST':
        try:
            # Update encrypted student data
            name = request.form['name']
            sex = request.form['sex']
            form_class = request.form['form_class']
            parent_phone = request.form['parent_phone']
            
            if student.school and student.school.encryption_key:
                student.name = encrypt_sensitive_field(name, student.school_id, student.school.encryption_key)
                student.sex = encrypt_sensitive_field(sex, student.school_id, student.school.encryption_key)
                student.form_class = encrypt_sensitive_field(form_class, student.school_id, student.school.encryption_key)
                if parent_phone:
                    student.parent_phone = encrypt_phone_field(parent_phone, student.school_id, student.school.encryption_key)
            else:
                student.name = name
                student.sex = sex
                student.form_class = form_class
                student.parent_phone = parent_phone
            

            
            db.session.commit()
            flash('Student details updated successfully!', 'success')
            return redirect(url_for('students'))
        except Exception as e:
            flash(f'Error updating student: {str(e)}', 'error')
    
    # Get active config for current school
    fund_config_query = get_school_filtered_query(FundConfiguration)
    active_config = fund_config_query.filter_by(is_active=True).first()
    
    # Decrypt student data for display
    student.decrypted_data = decrypt_student_data(student)
    
    return render_template('edit_student.html', student=student, active_config=active_config)

@app.route('/add_student', methods=['GET', 'POST'])
@login_required
def add_student():
    current_school_id = get_current_school_id()
    if not current_school_id:
        flash('No school access configured. Please contact administrator.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            student_id_input = request.form['student_id']
            name = request.form['name']
            sex = request.form['sex']
            form_class = request.form['form_class']
            parent_phone = request.form.get('parent_phone', '').strip() or None
            
            # Check if this ID already exists
            existing_student = Student.query.filter_by(school_id=current_school_id, student_id=student_id_input).first()
            if existing_student:
                flash('Student ID already exists. Please use a different ID.', 'error')
                return render_template('add_student.html', generated_id=generate_student_id())
            
            # Create student with basic information only
            student = Student(
                school_id=current_school_id,
                student_id=student_id_input,
                name=name,
                sex=sex,
                form_class=form_class,
                parent_phone=parent_phone
            )
            
            db.session.add(student)
            db.session.commit()
            
            flash(f'Student added successfully with ID: {student_id_input}!', 'success')
            return redirect(url_for('students'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding student: {str(e)}', 'error')
            return render_template('add_student.html', generated_id=generate_student_id())
    
    return render_template('add_student.html', generated_id=generate_student_id())

@app.route('/income')
@login_required
def income():
    # Get search parameters
    student_name = request.args.get('student_name', '').strip()
    form_class = request.args.get('form_class', '').strip()
    deposit_ref = request.args.get('deposit_ref', '').strip()

    # Get search parameters
    student_name = request.args.get('student_name', '').strip()
    form_class = request.args.get('form_class', '').strip()
    deposit_ref = request.args.get('deposit_ref', '').strip()

    # Developers should not see school data
    if session.get('user_role') == 'developer':
        flash('Access denied. Developers cannot view school data.', 'error')
        return redirect(url_for('manage_schools'))
    
    current_school_id = get_current_school_id()
    if not current_school_id:
        flash('No school access configured. Please contact administrator.', 'error')
        return redirect(url_for('logout'))
    
    # Get search parameters for template
    search_query = {
        'student_name': student_name,
        'form_class': form_class,
        'deposit_ref': deposit_ref
    }
    
    # Get active config for current school
    fund_config_query = get_school_filtered_query(FundConfiguration)
    active_config = fund_config_query.filter_by(is_active=True).first()
    PTA_EXPECTED = active_config.pta_amount if active_config else 45000
    SDF_EXPECTED = active_config.sdf_amount if active_config else 5000
    BOARDING_EXPECTED = active_config.boarding_amount if active_config else 0
    
    # Get school-filtered students (search on encrypted data won't work, so we'll filter after decryption)
    student_query = get_school_filtered_query(Student)
    all_students = student_query.all()
    
    # Filter students after decryption
    students = []
    for student in all_students:
        decrypted_data = decrypt_student_data(student)
        
        # Get last payment details including deposit reference
        income_query = get_school_filtered_query(Income)
        latest_income = income_query.filter_by(student_id=student.student_id).order_by(Income.payment_date.desc()).first()
        latest_deposit_ref = ''
        if latest_income and latest_income.payment_reference:
            if latest_income.school and latest_income.school.encryption_key:
                latest_deposit_ref = decrypt_sensitive_field(latest_income.payment_reference, latest_income.school_id, latest_income.school.encryption_key)
            else:
                latest_deposit_ref = latest_income.payment_reference
        
        # Apply search filters
        matches = True
        if student_name and student_name.lower() not in decrypted_data['name'].lower():
            matches = False
        if form_class and form_class.lower() not in decrypted_data['form_class'].lower():
            matches = False
        if deposit_ref and deposit_ref.lower() not in latest_deposit_ref.lower():
            matches = False
        
        if matches:
            # Add decrypted data to student object for template use
            student.decrypted_data = decrypted_data
            student.decrypted_student_id = decrypted_data['student_id']
            student.decrypted_name = decrypted_data['name']
            student.decrypted_sex = decrypted_data['sex']
            student.decrypted_form_class = decrypted_data['form_class']
            students.append(student)
    
    # Sort by decrypted name
    students.sort(key=lambda x: x.decrypted_data['name'])
    
    # Calculate totals from actual student payments (school-filtered)
    pta_total = db.session.query(db.func.sum(Student.pta_amount_paid)).filter_by(school_id=current_school_id).scalar() or 0
    sdf_total = db.session.query(db.func.sum(Student.sdf_amount_paid)).filter_by(school_id=current_school_id).scalar() or 0
    boarding_total = db.session.query(db.func.sum(Student.boarding_amount_paid)).filter_by(school_id=current_school_id).scalar() or 0
    
    # Get other income total (school-filtered)
    try:
        other_income_query = get_school_filtered_query(OtherIncome)
        other_income_total = other_income_query.with_entities(db.func.sum(OtherIncome.amount_paid)).scalar() or 0
        other_incomes = other_income_query.order_by(OtherIncome.date.desc()).all()
        
        # Decrypt other income data for display
        for other_income in other_incomes:
            if other_income.school and other_income.school.encryption_key:
                other_income.decrypted_customer_name = decrypt_sensitive_field(other_income.customer_name, other_income.school_id, other_income.school.encryption_key)
                other_income.decrypted_income_type = decrypt_sensitive_field(other_income.income_type, other_income.school_id, other_income.school.encryption_key)
            else:
                other_income.decrypted_customer_name = other_income.customer_name
                other_income.decrypted_income_type = other_income.income_type
    except Exception as e:
        print(f"Error fetching other income: {e}")
        other_income_total = 0
        other_incomes = []
    
    # Calculate grand total
    grand_total = pta_total + sdf_total + boarding_total + other_income_total
    
    # Create unique student records for display (no duplicates)
    student_records = []
    for student in students:
        # Use per-student required if set, else use config
        pta_expected = student.pta_required if student.pta_required else PTA_EXPECTED
        sdf_expected = student.sdf_required if student.sdf_required else SDF_EXPECTED
        boarding_expected = student.boarding_required if student.boarding_required else BOARDING_EXPECTED
        
        # Get latest payment date for this student
        income_query = get_school_filtered_query(Income)
        student_incomes = [inc for inc in income_query.all() if inc.student_id == student.student_id]
        latest_payment_date = max([inc.payment_date for inc in student_incomes]) if student_incomes else None
        
        # Get latest deposit reference
        latest_deposit_ref = None
        if student_incomes:
            latest_income = max(student_incomes, key=lambda x: x.payment_date)
            if latest_income.payment_reference:
                if latest_income.school and latest_income.school.encryption_key:
                    latest_deposit_ref = decrypt_sensitive_field(latest_income.payment_reference, latest_income.school_id, latest_income.school.encryption_key)
                else:
                    latest_deposit_ref = latest_income.payment_reference
        
        total_balance = (pta_expected + sdf_expected + boarding_expected) - (student.pta_amount_paid + student.sdf_amount_paid + student.boarding_amount_paid)
        
        student_records.append({
            'date': latest_payment_date,
            'student_id': student.decrypted_student_id,
            'student_name': student.decrypted_name,
            'sex': student.decrypted_sex,
            'form_class': student.decrypted_form_class,
            'deposit_ref_no': latest_deposit_ref or 'N/A',
            'pta_paid': student.pta_amount_paid,
            'sdf_paid': student.sdf_amount_paid,
            'boarding_paid': student.boarding_amount_paid,
            'balance': max(0, total_balance),
            'can_download_receipt': student.is_paid_in_full(),
            'student_db_id': student.id
        })
    
    return render_template(
        'income.html',
        pta_total=pta_total,
        sdf_total=sdf_total,
        boarding_total=boarding_total,
        other_income_total=other_income_total,
        grand_total=grand_total,
        other_incomes=other_incomes,
        search_query=search_query,
        recorded_payments=student_records
    )


# New route: Grouped income by student (PTA and SDF side by side)
@app.route('/income_grouped')
@login_required
def income_grouped():
    current_school_id = get_current_school_id()
    if not current_school_id and session.get('user_role') != 'developer':
        flash('No school access configured. Please contact administrator.', 'error')
        return redirect(url_for('logout'))
    
    # Get active fund configuration for current school
    fund_config_query = get_school_filtered_query(FundConfiguration)
    active_config = fund_config_query.filter_by(is_active=True).first()
    PTA_EXPECTED = active_config.pta_amount if active_config else 45000
    SDF_EXPECTED = active_config.sdf_amount if active_config else 5000
    BOARDING_EXPECTED = active_config.boarding_amount if active_config else 0
    # Get school-filtered students
    student_query = get_school_filtered_query(Student)
    students = student_query.all()
    
    # Decrypt and sort students
    for student in students:
        decrypted_data = decrypt_student_data(student)
        student.decrypted_data = decrypted_data
        student.decrypted_student_id = decrypted_data['student_id']
        student.decrypted_name = decrypted_data['name']
        student.decrypted_sex = decrypted_data['sex']
        student.decrypted_form_class = decrypted_data['form_class']
        student.decrypted_parent_phone = decrypted_data['parent_phone']
    
    students.sort(key=lambda x: x.decrypted_data['name'])
    for student in students:
        # Use per-student required if set, else use config
        student.pta_expected = student.pta_required if student.pta_required else PTA_EXPECTED
        student.sdf_expected = student.sdf_required if student.sdf_required else SDF_EXPECTED
        student.boarding_expected = student.boarding_required if student.boarding_required else BOARDING_EXPECTED
        student.pta_balance = max(0, student.pta_expected - student.pta_amount_paid)
        student.sdf_balance = max(0, student.sdf_expected - student.sdf_amount_paid)
        student.boarding_balance = max(0, student.boarding_expected - student.boarding_amount_paid)
        student.total_paid = student.pta_amount_paid + student.sdf_amount_paid + student.boarding_amount_paid
        student.total_balance = (student.pta_expected + student.sdf_expected + student.boarding_expected) - student.total_paid
        # Get last payment date and last deposit slip ref (school-filtered)
        income_query = get_school_filtered_query(Income)
        student_incomes = [inc for inc in income_query.all() if inc.student_id == student.student_id]
        last_income = max(student_incomes, key=lambda x: x.payment_date) if student_incomes else None
        
        student.last_payment_date = last_income.payment_date if last_income else None
        if last_income and last_income.payment_reference:
            if last_income.school and last_income.school.encryption_key:
                student.last_deposit_slip = decrypt_sensitive_field(last_income.payment_reference, last_income.school_id, last_income.school.encryption_key)
            else:
                student.last_deposit_slip = last_income.payment_reference
        else:
            student.last_deposit_slip = None
    return render_template('income_grouped.html', students=students)

@app.route('/edit_income/<int:student_id>', methods=['GET', 'POST'])
@login_required
def edit_income(student_id):
    current_school_id = get_current_school_id()
    if not current_school_id:
        flash('No school access configured. Please contact administrator.', 'error')
        return redirect(url_for('index'))
    
    # Get school-filtered student
    student_query = get_school_filtered_query(Student)
    student = student_query.filter_by(id=student_id).first_or_404()
    
    if request.method == 'POST':
        try:
            # Get the latest income record for deposit slip reference update
            income_query = get_school_filtered_query(Income)
            latest_income = income_query.filter_by(student_id=student.student_id).order_by(Income.created_at.desc()).first()
            
            # Update student payment amounts
            old_pta = student.pta_amount_paid
            old_sdf = student.sdf_amount_paid
            old_boarding = student.boarding_amount_paid
            
            student.pta_amount_paid = float(request.form.get('pta_amount_paid', 0) or 0)
            student.sdf_amount_paid = float(request.form.get('sdf_amount_paid', 0) or 0)
            student.boarding_amount_paid = float(request.form.get('boarding_amount_paid', 0) or 0)
            
            # Auto-generate payment reference if missing
            if latest_income and not latest_income.payment_reference:
                school = SchoolConfiguration.query.get(current_school_id)
                default_ref = f"REF{latest_income.id:06d}"
                if school and school.encryption_key:
                    latest_income.payment_reference = encrypt_sensitive_field(default_ref, current_school_id, school.encryption_key)
                else:
                    latest_income.payment_reference = default_ref
            
            db.session.commit()
            flash('Student payment information updated successfully!', 'success')
            return redirect(url_for('income'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating payment information: {str(e)}', 'error')
    
    # Auto-generate payment reference if missing for display
    income_query = get_school_filtered_query(Income)
    latest_income = income_query.filter_by(student_id=student.student_id).order_by(Income.created_at.desc()).first()
    
    # Decrypt student data for display
    decrypted_data = decrypt_student_data(student)
    student.decrypted_student_id = decrypted_data['student_id']
    student.decrypted_name = decrypted_data['name']
    student.decrypted_form_class = decrypted_data['form_class']
    
    return render_template('edit_income.html', student=student)

@app.route('/add_income', methods=['GET', 'POST'])
@login_required
def add_income():
    current_school_id = get_current_school_id()
    if not current_school_id:
        flash('No school access configured. Please contact administrator.', 'error')
        return redirect(url_for('index'))
    
    # Get school-filtered students and active config
    student_query = get_school_filtered_query(Student)
    students = student_query.all()
    
    # Set decrypted fields for template use
    for student in students:
        decrypted_data = decrypt_student_data(student)
        student.decrypted_student_id = decrypted_data['student_id']
        student.decrypted_name = decrypted_data['name']
        student.decrypted_sex = decrypted_data['sex']
        student.decrypted_form_class = decrypted_data['form_class']
    
    fund_config_query = get_school_filtered_query(FundConfiguration)
    active_config = fund_config_query.filter_by(is_active=True).first()
    
    # Convert students to JSON for JavaScript (with decrypted data)
    import json
    students_json = []
    for student in students:
        decrypted_data = decrypt_student_data(student)
        students_json.append({
            'student_id': decrypted_data['student_id'],
            'name': decrypted_data['name'],
            'pta_required': float(student.pta_required),
            'sdf_required': float(student.sdf_required),
            'boarding_required': float(student.boarding_required),
            'pta_amount_paid': float(student.pta_amount_paid),
            'sdf_amount_paid': float(student.sdf_amount_paid),
            'boarding_amount_paid': float(student.boarding_amount_paid),
            'pta_balance': float(student.get_pta_balance()),
            'sdf_balance': float(student.get_sdf_balance()),
            'boarding_balance': float(student.get_boarding_balance())
        })
    students_json = json.dumps(students_json)
    
    if request.method == 'POST':
        try:
            student_name = request.form['student_name_search']
            student_id = request.form['student_id']
            payment_date = request.form['payment_date']
            deposit_ref_no = request.form['deposit_ref_no']
            
            # Get payment amounts for each fee type
            pta_amount = float(request.form.get('pta_amount', 0) or 0)
            sdf_amount = float(request.form.get('sdf_amount', 0) or 0)
            boarding_amount = float(request.form.get('boarding_amount', 0) or 0)
            
            # Validate at least one payment
            if pta_amount + sdf_amount + boarding_amount <= 0:
                flash('Please enter at least one payment amount!', 'error')
                return render_template('add_income.html', students=students, active_config=active_config, students_json=students_json)
            
            # Get student (find by decrypted name)
            student = None
            for s in students:
                if decrypt_student_data(s)['name'] == student_name:
                    student = s
                    break
            
            if not student:
                flash('Student not found!', 'error')
                return render_template('add_income.html', students=students, active_config=active_config, students_json=students_json)
            
            # Process each fee type payment
            payments_made = []
            school = SchoolConfiguration.query.get(current_school_id)
            decrypted_student_data = decrypt_student_data(student)
            
            # PTA Payment
            if pta_amount > 0:
                # ...existing code...
                
                current_balance = student.get_pta_balance()
                if pta_amount > current_balance:
                    flash(f'PTA amount paid (MK {pta_amount:,.2f}) cannot exceed the remaining balance (MK {current_balance:,.2f})', 'error')
                    return render_template('add_income.html', students=students, active_config=active_config, students_json=students_json)
                
                student.pta_amount_paid += pta_amount
                student.pta_installments += 1
                payments_made.append(('PTA', pta_amount, student.get_pta_balance()))
            
            # SDF Payment
            if sdf_amount > 0:
                if not student.can_pay_installment('SDF'):
                    flash('Maximum SDF installments (2) already reached for this student!', 'error')
                    return render_template('add_income.html', students=students, active_config=active_config, students_json=students_json)
                
                current_balance = student.get_sdf_balance()
                if sdf_amount > current_balance:
                    flash(f'SDF amount paid (MK {sdf_amount:,.2f}) cannot exceed the remaining balance (MK {current_balance:,.2f})', 'error')
                    return render_template('add_income.html', students=students, active_config=active_config, students_json=students_json)
                
                student.sdf_amount_paid += sdf_amount
                student.sdf_installments += 1
                payments_made.append(('SDF', sdf_amount, student.get_sdf_balance()))
            
            # Boarding Payment
            if boarding_amount > 0:
                if not student.can_pay_installment('Boarding'):
                    flash('Maximum Boarding installments (2) already reached for this student!', 'error')
                    return render_template('add_income.html', students=students, active_config=active_config, students_json=students_json)
                
                current_balance = student.get_boarding_balance()
                if boarding_amount > current_balance:
                    flash(f'Boarding amount paid (MK {boarding_amount:,.2f}) cannot exceed the remaining balance (MK {current_balance:,.2f})', 'error')
                    return render_template('add_income.html', students=students, active_config=active_config, students_json=students_json)
                
                student.boarding_amount_paid += boarding_amount
                student.boarding_installments += 1
                payments_made.append(('Boarding', boarding_amount, student.get_boarding_balance()))
            
            # Create income and receipt records for each payment made
            plain_receipt_no = None
            for fee_type, amount, balance in payments_made:
                # Generate plain receipt number first
                plain_receipt_no = Receipt.generate_receipt_number(current_school_id)
                
                # Create income record
                income_record = Income(
                    school_id=current_school_id,
                    payment_date=datetime.strptime(payment_date, '%Y-%m-%d').date(),
                    amount_paid=float(amount),
                    balance=float(balance),
                    created_at=datetime.utcnow()
                )
                
                # Store data without encryption for now
                income_record.student_id = decrypted_student_data['student_id']
                income_record.student_name = decrypted_student_data['name']
                income_record.form_class = decrypted_student_data['form_class']
                income_record.payment_reference = deposit_ref_no
                income_record.fee_type = fee_type
                
                # Create receipt record
                receipt = Receipt(
                    school_id=current_school_id,
                    receipt_no=plain_receipt_no,
                    payment_date=datetime.strptime(payment_date, '%Y-%m-%d').date(),
                    amount_paid=float(amount),
                    balance=float(balance),
                    installment_number=student.pta_installments if fee_type == 'PTA' else (student.sdf_installments if fee_type == 'SDF' else student.boarding_installments)
                )
                
                # Store data without encryption for now
                receipt.student_id = decrypted_student_data['student_id']
                receipt.student_name = decrypted_student_data['name']
                receipt.form_class = decrypted_student_data['form_class']
                receipt.deposit_slip_ref = deposit_ref_no
                receipt.fee_type = fee_type
                
                db.session.add(income_record)
                db.session.add(receipt)
            db.session.commit()
            
            # Send SMS confirmation to parent if phone number exists (but don't let SMS errors affect the payment)
            try:
                if student.parent_phone:
                    payment_details = {
                        'amount': amount,
                        'fee_type': fee_type,
                        'receipt_no': plain_receipt_no,
                        'date': datetime.now().strftime('%B %d, %Y')
                    }
                    sms_result = sms_service.send_payment_confirmation(student, student.parent_phone, payment_details)
                    if sms_result.get('success'):
                        flash(f'Payment recorded successfully! Receipt No: {plain_receipt_no}. SMS sent to parent.', 'success')
                    else:
                        flash(f'Payment recorded successfully! Receipt No: {plain_receipt_no}. SMS notification failed but payment was saved.', 'success')
                else:
                    flash(f'Payment recorded successfully! Receipt No: {plain_receipt_no}', 'success')
            except Exception as sms_error:
                # SMS error should not affect payment success
                flash(f'Payment recorded successfully! Receipt No: {plain_receipt_no}', 'success')
            
            return redirect(url_for('income'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error recording payment: {str(e)}', 'error')
            return render_template('add_income.html', students=students, active_config=active_config, students_json=students_json)
    
    return render_template('add_income.html', students=students, active_config=active_config, students_json=students_json)

@app.route('/expenditure')
@login_required
def expenditure():
    # Developers should not see school data
    if session.get('user_role') == 'developer':
        flash('Access denied. Developers cannot view school data.', 'error')
        return redirect(url_for('manage_schools'))
    
    current_school_id = get_current_school_id()
    if not current_school_id:
        flash('No school access configured. Please contact administrator.', 'error')
        return redirect(url_for('index'))
    
    # Get school-filtered expenditures
    expenditure_query = get_school_filtered_query(Expenditure)
    expenditures = expenditure_query.order_by(Expenditure.date.desc()).all()
    
    # Calculate total collections from students (school-filtered)
    if current_school_id:
        pta_collected = db.session.query(db.func.sum(Student.pta_amount_paid)).filter_by(school_id=current_school_id).scalar() or 0
        sdf_collected = db.session.query(db.func.sum(Student.sdf_amount_paid)).filter_by(school_id=current_school_id).scalar() or 0
        boarding_collected = db.session.query(db.func.sum(Student.boarding_amount_paid)).filter_by(school_id=current_school_id).scalar() or 0
        other_income_collected = db.session.query(db.func.sum(OtherIncome.amount_paid)).filter_by(school_id=current_school_id).scalar() or 0
        pta_expenditure = db.session.query(db.func.sum(Expenditure.amount_paid)).filter_by(school_id=current_school_id, fund_type='PTA').scalar() or 0
        sdf_expenditure = db.session.query(db.func.sum(Expenditure.amount_paid)).filter_by(school_id=current_school_id, fund_type='SDF').scalar() or 0
        boarding_expenditure = db.session.query(db.func.sum(Expenditure.amount_paid)).filter_by(school_id=current_school_id, fund_type='Boarding').scalar() or 0
        other_income_expenditure = db.session.query(db.func.sum(Expenditure.amount_paid)).filter_by(school_id=current_school_id, fund_type='Other Income').scalar() or 0
    else:
        # Developer view - all schools
        pta_collected = db.session.query(db.func.sum(Student.pta_amount_paid)).scalar() or 0
        sdf_collected = db.session.query(db.func.sum(Student.sdf_amount_paid)).scalar() or 0
        boarding_collected = db.session.query(db.func.sum(Student.boarding_amount_paid)).scalar() or 0
        other_income_collected = db.session.query(db.func.sum(OtherIncome.amount_paid)).scalar() or 0
        pta_expenditure = db.session.query(db.func.sum(Expenditure.amount_paid)).filter_by(fund_type='PTA').scalar() or 0
        sdf_expenditure = db.session.query(db.func.sum(Expenditure.amount_paid)).filter_by(fund_type='SDF').scalar() or 0
        boarding_expenditure = db.session.query(db.func.sum(Expenditure.amount_paid)).filter_by(fund_type='Boarding').scalar() or 0
        other_income_expenditure = db.session.query(db.func.sum(Expenditure.amount_paid)).filter_by(fund_type='Other Income').scalar() or 0
    
    # Calculate remaining balances
    pta_balance = pta_collected - pta_expenditure
    sdf_balance = sdf_collected - sdf_expenditure
    boarding_balance = boarding_collected - boarding_expenditure
    other_income_balance = other_income_collected - other_income_expenditure
    
    return render_template('expenditure.html', 
                         expenditures=expenditures, 
                         pta_collected=pta_collected,
                         sdf_collected=sdf_collected,
                         boarding_collected=boarding_collected,
                         other_income_collected=other_income_collected,
                         pta_expenditure=pta_expenditure,
                         sdf_expenditure=sdf_expenditure,
                         boarding_expenditure=boarding_expenditure,
                         other_income_expenditure=other_income_expenditure,
                         pta_balance=pta_balance,
                         sdf_balance=sdf_balance,
                         boarding_balance=boarding_balance,
                         other_income_balance=other_income_balance)

@app.route('/add_expenditure', methods=['GET', 'POST'])
@login_required
def add_expenditure():
    current_school_id = get_current_school_id()
    if not current_school_id:
        flash('No school access configured. Please contact administrator.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            expenditure = Expenditure(
                school_id=current_school_id,
                date=datetime.strptime(request.form['date'], '%Y-%m-%d').date(),
                activity_service=request.form['activity_service'],
                voucher_no=request.form['voucher_no'],
                cheque_no=request.form['cheque_no'],
                amount_paid=float(request.form['amount_paid']),
                fund_type=request.form['fund_type']
            )
            db.session.add(expenditure)
            db.session.commit()
            flash('Expenditure recorded successfully!', 'success')
            return redirect(url_for('expenditure'))
        except Exception as e:
            flash(f'Error recording expenditure: {str(e)}', 'error')
    return render_template('add_expenditure.html')

@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html')

@app.route('/daily_report')
@login_required
def daily_report():
    # Developers should not see school data
    if session.get('user_role') == 'developer':
        flash('Access denied. Developers cannot view school data.', 'error')
        return redirect(url_for('manage_schools'))
    
    current_school_id = get_current_school_id()
    if not current_school_id:
        flash('No school access configured. Please contact administrator.', 'error')
        return redirect(url_for('index'))
    
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    report_date = datetime.strptime(date, '%Y-%m-%d').date()
    
    # Get school-filtered income records for the specific date
    income_query = get_school_filtered_query(Income)
    daily_income = income_query.filter_by(payment_date=report_date).all()
    
    # Get school-filtered expenditure records for the specific date
    expenditure_query = get_school_filtered_query(Expenditure)
    daily_expenditure = expenditure_query.filter_by(date=report_date).all()
    
    # Get school-filtered other income for the specific date
    try:
        other_income_query = get_school_filtered_query(OtherIncome)
        daily_other_income = other_income_query.filter_by(date=report_date).all()
        daily_other_income_total = sum(oi.amount_paid for oi in daily_other_income)
        total_other_income = db.session.query(db.func.sum(OtherIncome.amount_paid)).filter_by(school_id=current_school_id).scalar() or 0
    except:
        daily_other_income = []
        daily_other_income_total = 0
        total_other_income = 0
    
    # Calculate totals from Income table (cumulative totals) - school-filtered
    pta_collected = db.session.query(db.func.sum(Income.amount_paid)).filter_by(school_id=current_school_id, fee_type='PTA').scalar() or 0
    sdf_collected = db.session.query(db.func.sum(Income.amount_paid)).filter_by(school_id=current_school_id, fee_type='SDF').scalar() or 0
    boarding_collected = db.session.query(db.func.sum(Income.amount_paid)).filter_by(school_id=current_school_id, fee_type='Boarding').scalar() or 0
    
    # Calculate income collected for the specific date
    pta_income = sum(i.amount_paid for i in daily_income if i.fee_type == 'PTA')
    sdf_income = sum(i.amount_paid for i in daily_income if i.fee_type == 'SDF')
    boarding_income = sum(i.amount_paid for i in daily_income if i.fee_type == 'Boarding')
    
    # Calculate total expenditure by fund type - school-filtered
    total_pta_expenditure = db.session.query(db.func.sum(Expenditure.amount_paid)).filter_by(school_id=current_school_id, fund_type='PTA').scalar() or 0
    total_sdf_expenditure = db.session.query(db.func.sum(Expenditure.amount_paid)).filter_by(school_id=current_school_id, fund_type='SDF').scalar() or 0
    total_boarding_expenditure = db.session.query(db.func.sum(Expenditure.amount_paid)).filter_by(school_id=current_school_id, fund_type='Boarding').scalar() or 0
    
    # Calculate expenditure for the specific date
    daily_pta_expenditure = sum(e.amount_paid for e in daily_expenditure if e.fund_type == 'PTA')
    daily_sdf_expenditure = sum(e.amount_paid for e in daily_expenditure if e.fund_type == 'SDF')
    daily_boarding_expenditure = sum(e.amount_paid for e in daily_expenditure if e.fund_type == 'Boarding')
    
    # Calculate remaining balances
    pta_balance = pta_collected - total_pta_expenditure
    sdf_balance = sdf_collected - total_sdf_expenditure
    boarding_balance = boarding_collected - total_boarding_expenditure
    
    return render_template('daily_report.html', 
                         date=report_date,
                         daily_income=daily_income,
                         daily_expenditure=daily_expenditure,
                         daily_other_income=daily_other_income,
                         daily_other_income_total=daily_other_income_total,
                         total_other_income=total_other_income,
                         pta_collected=pta_collected,
                         sdf_collected=sdf_collected,
                         boarding_collected=boarding_collected,
                         pta_income=pta_collected,
                         sdf_income=sdf_collected,
                         boarding_income=boarding_collected,
                         pta_expenditure=daily_pta_expenditure,
                         sdf_expenditure=daily_sdf_expenditure,
                         boarding_expenditure=daily_boarding_expenditure,
                         total_pta_expenditure=total_pta_expenditure,
                         total_sdf_expenditure=total_sdf_expenditure,
                         total_boarding_expenditure=total_boarding_expenditure,
                         pta_balance=pta_balance,
                         sdf_balance=sdf_balance,
                         boarding_balance=boarding_balance)

@app.route('/weekly_report')
@login_required
def weekly_report():
    # Developers should not see school data
    if session.get('user_role') == 'developer':
        flash('Access denied. Developers cannot view school data.', 'error')
        return redirect(url_for('manage_schools'))
    
    current_school_id = get_current_school_id()
    if not current_school_id:
        flash('No school access configured. Please contact administrator.', 'error')
        return redirect(url_for('index'))
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=6)
    
    # Get school-filtered income and expenditure records for the week
    income_query = get_school_filtered_query(Income)
    expenditure_query = get_school_filtered_query(Expenditure)
    weekly_income = income_query.filter(
        Income.payment_date >= start_date,
        Income.payment_date <= end_date
    ).all()
    
    weekly_expenditure = expenditure_query.filter(
        Expenditure.date >= start_date,
        Expenditure.date <= end_date
    ).all()
    
    # Get school-filtered other income for the week
    try:
        other_income_query = get_school_filtered_query(OtherIncome)
        weekly_other_income = other_income_query.filter(
            OtherIncome.date >= start_date,
            OtherIncome.date <= end_date
        ).all()
        weekly_other_income_total = sum(oi.amount_paid for oi in weekly_other_income)
        total_other_income = db.session.query(db.func.sum(OtherIncome.amount_paid)).filter_by(school_id=current_school_id).scalar() or 0
    except:
        weekly_other_income = []
        weekly_other_income_total = 0
        total_other_income = 0
    
    # Calculate totals from Income table (cumulative totals)
    pta_collected = db.session.query(db.func.sum(Income.amount_paid)).filter_by(fee_type='PTA').scalar() or 0
    sdf_collected = db.session.query(db.func.sum(Income.amount_paid)).filter_by(fee_type='SDF').scalar() or 0
    boarding_collected = db.session.query(db.func.sum(Income.amount_paid)).filter_by(fee_type='Boarding').scalar() or 0
    
    # Calculate total expenditures (cumulative) - school-filtered
    pta_collected = db.session.query(db.func.sum(Income.amount_paid)).filter_by(school_id=current_school_id, fee_type='PTA').scalar() or 0
    sdf_collected = db.session.query(db.func.sum(Income.amount_paid)).filter_by(school_id=current_school_id, fee_type='SDF').scalar() or 0
    boarding_collected = db.session.query(db.func.sum(Income.amount_paid)).filter_by(school_id=current_school_id, fee_type='Boarding').scalar() or 0
    total_pta_expenditure = db.session.query(db.func.sum(Expenditure.amount_paid)).filter_by(school_id=current_school_id, fund_type='PTA').scalar() or 0
    total_sdf_expenditure = db.session.query(db.func.sum(Expenditure.amount_paid)).filter_by(school_id=current_school_id, fund_type='SDF').scalar() or 0
    total_boarding_expenditure = db.session.query(db.func.sum(Expenditure.amount_paid)).filter_by(school_id=current_school_id, fund_type='Boarding').scalar() or 0
    
    # Calculate expenditure for the week
    weekly_pta_expenditure = sum(e.amount_paid for e in weekly_expenditure if e.fund_type == 'PTA')
    weekly_sdf_expenditure = sum(e.amount_paid for e in weekly_expenditure if e.fund_type == 'SDF')
    weekly_boarding_expenditure = sum(e.amount_paid for e in weekly_expenditure if e.fund_type == 'Boarding')
    
    # Calculate remaining balances
    pta_balance = pta_collected - total_pta_expenditure
    sdf_balance = sdf_collected - total_sdf_expenditure
    boarding_balance = boarding_collected - total_boarding_expenditure
    
    return render_template('weekly_report.html',
                         start_date=start_date,
                         end_date=end_date,
                         weekly_income=weekly_income,
                         weekly_expenditure=weekly_expenditure,
                         weekly_other_income=weekly_other_income,
                         weekly_other_income_total=weekly_other_income_total,
                         total_other_income=total_other_income,
                         pta_collected=pta_collected,
                         sdf_collected=sdf_collected,
                         boarding_collected=boarding_collected,
                         pta_income=pta_collected,
                         sdf_income=sdf_collected,
                         boarding_income=boarding_collected,
                         pta_expenditure=weekly_pta_expenditure,
                         sdf_expenditure=weekly_sdf_expenditure,
                         boarding_expenditure=weekly_boarding_expenditure,
                         total_pta_expenditure=total_pta_expenditure,
                         total_sdf_expenditure=total_sdf_expenditure,
                         total_boarding_expenditure=total_boarding_expenditure,
                         pta_balance=pta_balance,
                         sdf_balance=sdf_balance,
                         boarding_balance=boarding_balance)

@app.route('/payment_status')
@login_required
def payment_status():
    # Developers should not see school data
    if session.get('user_role') == 'developer':
        flash('Access denied. Developers cannot view school data.', 'error')
        return redirect(url_for('manage_schools'))
    
    current_school_id = get_current_school_id()
    if not current_school_id:
        flash('No school access configured. Please contact administrator.', 'error')
        return redirect(url_for('index'))
    
    # Get school-filtered students
    student_query = get_school_filtered_query(Student)
    all_students = student_query.all()
    
    # Decrypt student data and categorize
    paid_in_full = []
    outstanding = []
    
    for student in all_students:
        decrypted_data = decrypt_student_data(student)
        student.decrypted_student_id = decrypted_data['student_id']
        student.decrypted_name = decrypted_data['name']
        student.decrypted_sex = decrypted_data['sex']
        student.decrypted_form_class = decrypted_data['form_class']
        student.decrypted_parent_phone = decrypted_data['parent_phone']
        
        if student.is_paid_in_full():
            paid_in_full.append(student)
        else:
            outstanding.append(student)
    
    return render_template('payment_status.html', 
                         paid_in_full=paid_in_full,
                         outstanding=outstanding)

# Redirect old receipt route to new professional receipt
@app.route('/generate_receipt/<student_id>')
@login_required
def generate_receipt(student_id):
    return redirect(url_for('print_professional_receipt', student_id=student_id))

@app.route('/print_multiple_receipts')
@login_required
def print_multiple_receipts():
    """Print multiple receipts (up to 4 per page, arranged 2x2)."""
    current_school_id = get_current_school_id()
    if not current_school_id and session.get('user_role') != 'developer':
        flash('No school access configured. Please contact administrator.', 'error')
        return redirect(url_for('index'))
    
    # Get student IDs from query parameters
    student_ids = request.args.getlist('student_id')
    if not student_ids:
        flash('No students selected for receipt generation.', 'error')
        return redirect(url_for('payment_status'))
    
    # Normalize student_ids: accept either multiple student_id params or a single comma-separated value
    flat_ids = []
    for sid in student_ids:
        if isinstance(sid, str) and ',' in sid:
            parts = [p.strip() for p in sid.split(',') if p.strip()]
            flat_ids.extend(parts)
        elif sid:
            flat_ids.append(sid)

    # Limit to 4 receipts per page (2x2 grid)
    student_ids = flat_ids[:4]
    
    receipts_data = []
    
    for student_id in student_ids:
        # Get school-filtered students and find by student_id
        student_query = get_school_filtered_query(Student)
        students = student_query.all()
        student = None
        for s in students:
            if s.student_id == student_id:
                student = s
                break
        
        if not student:
            continue

        # If student isn't paid in full, try to build a receipt from latest Income record
        use_income_record = None
        if not student.is_paid_in_full():
            income_query = get_school_filtered_query(Income)
            latest_income = income_query.filter_by(student_id=student.student_id).order_by(Income.payment_date.desc()).first()
            if latest_income:
                use_income_record = latest_income
        
        # Check if receipt already exists for this student
        existing_receipt = ProfessionalReceipt.query.filter_by(
            school_id=current_school_id, 
            student_id=student.student_id
        ).first()
        
        if existing_receipt:
            receipt_no = existing_receipt.receipt_no
            deposit_ref = existing_receipt.reference_number
        else:
            # Generate new receipt number
            existing_receipts = ProfessionalReceipt.query.filter_by(school_id=current_school_id).count()
            receipt_no = f"{existing_receipts + 1:03d}"
            
            # Get reference number from latest income record
            deposit_ref = None
            if use_income_record and use_income_record.payment_reference:
                if use_income_record.school and use_income_record.school.encryption_key:
                    deposit_ref = decrypt_sensitive_field(use_income_record.payment_reference, use_income_record.school_id, use_income_record.school.encryption_key)
                else:
                    deposit_ref = use_income_record.payment_reference
            else:
                # Fallback: try any income record
                income_query = get_school_filtered_query(Income)
                latest_income = income_query.filter_by(student_id=student.student_id).order_by(Income.payment_date.desc()).first()
                if latest_income and latest_income.payment_reference:
                    if latest_income.school and latest_income.school.encryption_key:
                        deposit_ref = decrypt_sensitive_field(latest_income.payment_reference, latest_income.school_id, latest_income.school.encryption_key)
                    else:
                        deposit_ref = latest_income.payment_reference
            
            # Create professional receipt record
            professional_receipt = ProfessionalReceipt(
                school_id=current_school_id,
                receipt_no=receipt_no,
                student_id=student.student_id,
                pta_amount=student.pta_amount_paid,
                sdf_amount=student.sdf_amount_paid,
                boarding_amount=student.boarding_amount_paid,
                reference_number=deposit_ref
            )
            db.session.add(professional_receipt)
        
        # Decrypt student data for display
        decrypted_data = decrypt_student_data(student)
        
        # If using an income record (partial payment), use those amounts instead
        if use_income_record:
            pta_amt = use_income_record.pta_amount or 0.0
            sdf_amt = use_income_record.sdf_amount or 0.0
            boarding_amt = use_income_record.boarding_amount or 0.0
            total_amt = (pta_amt or 0.0) + (sdf_amt or 0.0) + (boarding_amt or 0.0)
        else:
            pta_amt = student.pta_amount_paid or 0.0
            sdf_amt = student.sdf_amount_paid or 0.0
            boarding_amt = student.boarding_amount_paid or 0.0
            total_amt = (pta_amt or 0.0) + (sdf_amt or 0.0) + (boarding_amt or 0.0)

        receipts_data.append({
            'receipt_no': receipt_no,
            'student_id': decrypted_data['student_id'],
            'student_name': decrypted_data['name'],
            'form_class': decrypted_data['form_class'],
            'date': dt.now().strftime('%Y-%m-%d'),
            'deposit_ref': deposit_ref or 'N/A',
            'pta_amount': pta_amt,
            'sdf_amount': sdf_amt,
            'boarding_amount': boarding_amt,
            'total_amount': total_amt
        })
    
    if receipts_data:
        db.session.commit()
    
    # Get school configuration
    school_config = SchoolConfiguration.query.filter_by(id=current_school_id, is_active=True).first()
    school_name = school_config.school_name if school_config else 'School Name'
    school_address = school_config.school_address if school_config and school_config.school_address else None
    
    # Get active fund configuration
    fund_config_query = get_school_filtered_query(FundConfiguration)
    active_config = fund_config_query.filter_by(is_active=True).first()
    term_name = active_config.term_name if active_config else 'Current Term'
    
    return render_template(
        'multiple_receipts.html',
        receipts=receipts_data,
        school_name=school_name,
        school_address=school_address,
        term=term_name
    )

@app.route('/fund_config')
@login_required
def fund_config():
    current_school_id = get_current_school_id()
    if not current_school_id and session.get('user_role') != 'developer':
        flash('No school access configured. Please contact administrator.', 'error')
        return redirect(url_for('index'))
    
    # Get school-filtered configurations
    fund_config_query = get_school_filtered_query(FundConfiguration)
    configs = fund_config_query.order_by(FundConfiguration.created_at.desc()).all()
    active_config = fund_config_query.filter_by(is_active=True).first()
    
    # Get school for decryption
    school = SchoolConfiguration.query.filter_by(id=current_school_id).first() if current_school_id else None
    
    # Show raw term names (disable decryption)
    for config in configs:
        config.decrypted_term_name = config.term_name
    
    # Show raw term name for active config (disable decryption)
    if active_config:
        active_config.decrypted_term_name = active_config.term_name
    
    return render_template('fund_config.html', configs=configs, active_config=active_config)

@app.route('/add_fund_config', methods=['GET', 'POST'])
@login_required
def add_fund_config():
    current_school_id = get_current_school_id()
    if not current_school_id:
        flash('No school access configured. Please contact administrator.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            # Deactivate all existing configs for current school only
            fund_config_query = get_school_filtered_query(FundConfiguration)
            fund_config_query.update({'is_active': False})
            
            # Get school and encryption key
            school = SchoolConfiguration.query.filter_by(id=current_school_id).first()
            
            # Create new active config for current school
            config = FundConfiguration(
                school_id=current_school_id,
                pta_amount=float(request.form.get('pta_amount', 0.0)),  # Default to 0.0 if empty
                sdf_amount=float(request.form.get('sdf_amount', 0.0)),  # Default to 0.0 if empty
                boarding_amount=float(request.form.get('boarding_amount', 0.0)),  # Default to 0.0 if empty
                is_active=True
            )
            
            # Store raw term name (no encryption)
            term_name = request.form['term_name']
            config.term_name = term_name
            
            db.session.add(config)
            db.session.commit()
            flash('Fund configuration updated successfully!', 'success')
            return redirect(url_for('fund_config'))
        except Exception as e:
            flash(f'Error updating fund configuration: {str(e)}', 'error')
    return render_template('add_fund_config.html')

@app.route('/edit_fund_config/<int:config_id>', methods=['GET', 'POST'])
@login_required
def edit_fund_config(config_id):
    current_school_id = get_current_school_id()
    if not current_school_id:
        flash('No school access configured. Please contact administrator.', 'error')
        return redirect(url_for('index'))
    
    # Get school-filtered configuration
    fund_config_query = get_school_filtered_query(FundConfiguration)
    config = fund_config_query.filter_by(id=config_id).first()
    
    if not config:
        flash('Fund configuration not found!', 'error')
        return redirect(url_for('fund_config'))
    
    # Get school for decryption
    school = SchoolConfiguration.query.filter_by(id=current_school_id).first()
    
    if request.method == 'POST':
        try:
            # Get school and encryption key
            school = SchoolConfiguration.query.filter_by(id=current_school_id).first()
            
            # Update configuration
            config.pta_amount = float(request.form.get('pta_amount', 0.0))
            config.sdf_amount = float(request.form.get('sdf_amount', 0.0))
            config.boarding_amount = float(request.form.get('boarding_amount', 0.0))
            
            # Store raw term name (no encryption)
            term_name = request.form['term_name']
            config.term_name = term_name
            
            db.session.commit()
            flash('Fund configuration updated successfully!', 'success')
            return redirect(url_for('fund_config'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating fund configuration: {str(e)}', 'error')
    
    # Show raw term name (disable decryption)
    decrypted_term_name = config.term_name
    
    return render_template('edit_fund_config.html', config=config, decrypted_term_name=decrypted_term_name)

@app.route('/delete_fund_config/<int:config_id>', methods=['POST'])
@login_required
def delete_fund_config(config_id):
    current_school_id = get_current_school_id()
    if not current_school_id:
        flash('No school access configured. Please contact administrator.', 'error')
        return redirect(url_for('index'))
    
    try:
        # Get school-filtered configuration
        fund_config_query = get_school_filtered_query(FundConfiguration)
        config = fund_config_query.filter_by(id=config_id).first()
        
        if not config:
            flash('Fund configuration not found!', 'error')
            return redirect(url_for('fund_config'))
        
        # Get school for decryption to show term name in message
        school = SchoolConfiguration.query.filter_by(id=current_school_id).first()
        if school and school.encryption_key:
            term_name = decrypt_sensitive_field(config.term_name, current_school_id, school.encryption_key)
        else:
            term_name = config.term_name
        
        # Check if this is the active configuration
        if config.is_active:
            flash(f'Cannot delete active configuration "{term_name}". Please activate another configuration first.', 'error')
            return redirect(url_for('fund_config'))
        
        db.session.delete(config)
        db.session.commit()
        flash(f'Fund configuration "{term_name}" deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting fund configuration: {str(e)}', 'error')
    
    return redirect(url_for('fund_config'))

@app.route('/activate_fund_config/<int:config_id>', methods=['POST'])
@login_required
def activate_fund_config(config_id):
    current_school_id = get_current_school_id()
    if not current_school_id:
        flash('No school access configured. Please contact administrator.', 'error')
        return redirect(url_for('index'))
    
    try:
        # Get school-filtered configuration
        fund_config_query = get_school_filtered_query(FundConfiguration)
        config = fund_config_query.filter_by(id=config_id).first()
        
        if not config:
            flash('Fund configuration not found!', 'error')
            return redirect(url_for('fund_config'))
        
        # Get school for decryption to show term name in message
        school = SchoolConfiguration.query.filter_by(id=current_school_id).first()
        if school and school.encryption_key:
            term_name = decrypt_sensitive_field(config.term_name, current_school_id, school.encryption_key)
        else:
            term_name = config.term_name
        
        # Deactivate all other configurations for this school
        fund_config_query.update({'is_active': False})
        
        # Activate this configuration
        config.is_active = True
        
        db.session.commit()
        flash(f'Fund configuration "{term_name}" activated successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error activating fund configuration: {str(e)}', 'error')
    
    return redirect(url_for('fund_config'))

@app.route('/api/generate_student_id')
@login_required
def api_generate_student_id():
    """API endpoint to generate a new student ID"""
    try:
        new_id = generate_student_id()
        return jsonify({'student_id': new_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/send_sms_reminders', methods=['POST'])
@login_required
def send_sms_reminders():
    # Get school-filtered students
    student_query = get_school_filtered_query(Student)
    all_students = student_query.all()
    outstanding = [student for student in all_students if not student.is_paid_in_full()]
    
    reminders = []
    for student in outstanding:
        if student.parent_phone:
            pta_balance = student.get_pta_balance()
            sdf_balance = student.get_sdf_balance()
            boarding_balance = student.get_boarding_balance()
            fee_details = []
            if pta_balance > 0:
                fee_details.append(f"PTA: MK{pta_balance:.2f}")
            if sdf_balance > 0:
                fee_details.append(f"SDF: MK{sdf_balance:.2f}")
            if boarding_balance > 0:
                fee_details.append(f"Boarding: MK{boarding_balance:.2f}")
            
            if fee_details:
                message = f"Dear Parent, {student.name} has outstanding fees. {', '.join(fee_details)}. Please pay to avoid inconvenience."
            else:
                continue  # Skip if no outstanding fees
            reminders.append({
                'student': student.name,
                'phone': student.parent_phone,
                'message': message
            })
    
    return jsonify({'reminders': reminders, 'count': len(reminders)})

@app.route('/api/student_details/<student_type>')
@login_required
def api_student_details(student_type):
    """API endpoint to get student details for dashboard modals with tenant isolation"""
    # Enhanced tenant validation for API
    current_school_id = get_current_school_id()
    if not current_school_id and session.get('user_role') != 'developer':
        return jsonify({'error': 'Access denied. No school context.'}), 403
    
    # Get school-filtered students
    student_query = get_school_filtered_query(Student)
    all_students = student_query.all()
    
    # Determine students set based on balances to ensure counts sum to total
    if student_type == 'total':
        students = all_students
    elif student_type == 'paid':
        # Fully paid: all balances zero
        students = [s for s in all_students if s.get_pta_balance() == 0 and s.get_sdf_balance() == 0 and s.get_boarding_balance() == 0]
    elif student_type == 'outstanding':
        # Partial payments exist but some balances remain
        students = [s for s in all_students if (s.get_pta_balance() > 0 or s.get_sdf_balance() > 0 or s.get_boarding_balance() > 0) and (s.pta_amount_paid > 0 or s.sdf_amount_paid > 0 or s.boarding_amount_paid > 0)]
    elif student_type == 'no_payment':
        # No payments made at all
        students = [s for s in all_students if s.pta_amount_paid == 0 and s.sdf_amount_paid == 0 and s.boarding_amount_paid == 0]
    elif student_type == 'net_summary':
        students = all_students  # We'll filter in the loop below
    else:
        return jsonify({'error': 'Invalid student type'}), 400
    
    student_data = []
    for student in students:
        pta_balance = student.get_pta_balance()
        sdf_balance = student.get_sdf_balance()
        boarding_balance = student.get_boarding_balance()
        
        # For today's net, show consolidated payment info
        if student_type == 'net_summary':
            # Only include students who have made payments
            if student.pta_amount_paid > 0 or student.sdf_amount_paid > 0 or student.boarding_amount_paid > 0:
                student_data.append({
                    'student_id': student.student_id,
                    'name': student.name,
                    'form_class': student.form_class,
                    'total_paid': f'{student.pta_amount_paid + student.sdf_amount_paid + student.boarding_amount_paid:.2f}',
                    'pta_paid': f'{student.pta_amount_paid:.2f}',
                    'sdf_paid': f'{student.sdf_amount_paid:.2f}',
                    'boarding_paid': f'{student.boarding_amount_paid:.2f}'
                })
        else:
            student_data.append({
                'student_id': student.student_id,
                'name': student.name,
                'form_class': student.form_class,
                'pta_amount_paid': f'{student.pta_amount_paid:.2f}',
                'sdf_amount_paid': f'{student.sdf_amount_paid:.2f}',
                'boarding_amount_paid': f'{student.boarding_amount_paid:.2f}',
                'pta_status': 'Paid' if pta_balance == 0 else 'Outstanding',
                'sdf_status': 'Paid' if sdf_balance == 0 else 'Outstanding',
                'boarding_status': 'Paid' if boarding_balance == 0 else 'Outstanding',
                'total_outstanding': f'{pta_balance + sdf_balance + boarding_balance:.2f}'
            })
    
    return jsonify({'students': student_data})


@app.route('/debug/student_status_counts')
@login_required
def debug_student_status_counts():
    """Debug endpoint returning counts and sample students for Paid, Outstanding, and No Payment.
    This helps verify Paid + Outstanding + No Payment == Total Students using balance-driven logic.
    """
    # Tenant check
    current_school_id = get_current_school_id()
    if not current_school_id and session.get('user_role') != 'developer':
        return jsonify({'error': 'Access denied. No school context.'}), 403

    student_query = get_school_filtered_query(Student)
    all_students = student_query.all()

    total = len(all_students)
    paid = []
    no_payment = []
    outstanding = []

    for s in all_students:
        # Paid amounts (what has been paid so far)
        pta_paid = float(s.pta_amount_paid or 0)
        sdf_paid = float(s.sdf_amount_paid or 0)
        boarding_paid = float(s.boarding_amount_paid or 0)

        # Balances (what remains to be paid) using model helpers
        pta_bal = float(s.get_pta_balance() or 0)
        sdf_bal = float(s.get_sdf_balance() or 0)
        boarding_bal = float(s.get_boarding_balance() or 0)

        # Classification rules (mutually exclusive)
        if pta_paid == 0 and sdf_paid == 0 and boarding_paid == 0:
            no_payment.append(s)
        elif pta_bal == 0 and sdf_bal == 0 and boarding_bal == 0:
            paid.append(s)
        else:
            outstanding.append(s)

    def sample_list(lst, limit=10):
        out = []
        for st in lst[:limit]:
            try:
                dec = decrypt_student_data(st)
                out.append({
                    'student_id': dec.get('student_id'),
                    'name': dec.get('name'),
                    'form_class': dec.get('form_class'),
                    'pta_paid': float(st.pta_amount_paid or 0),
                    'sdf_paid': float(st.sdf_amount_paid or 0),
                    'boarding_paid': float(st.boarding_amount_paid or 0),
                    'pta_balance': float(st.get_pta_balance() or 0),
                    'sdf_balance': float(st.get_sdf_balance() or 0),
                    'boarding_balance': float(st.get_boarding_balance() or 0)
                })
            except Exception:
                out.append({'student_id': st.student_id, 'note': 'decrypt error'})
        return out

    result = {
        'total': total,
        'paid_count': len(paid),
        'outstanding_count': len(outstanding),
        'no_payment_count': len(no_payment),
        'paid_sample': sample_list(paid),
        'outstanding_sample': sample_list(outstanding),
        'no_payment_sample': sample_list(no_payment)
    }

    return jsonify(result)

@app.route('/api/todays_financial_summary')
@login_required
def api_todays_financial_summary():
    """API endpoint to get today's financial summary for dashboard"""
    current_school_id = get_current_school_id()
    today = datetime.now().date()
    
    # Get totals (school-filtered) - include all other income to balance to 110,000
    total_pta_income = db.session.query(db.func.sum(Student.pta_amount_paid)).filter_by(school_id=current_school_id).scalar() or 0
    total_sdf_income = db.session.query(db.func.sum(Student.sdf_amount_paid)).filter_by(school_id=current_school_id).scalar() or 0
    total_boarding_income = db.session.query(db.func.sum(Student.boarding_amount_paid)).filter_by(school_id=current_school_id).scalar() or 0
    total_other_income = db.session.query(db.func.sum(OtherIncome.amount_paid)).filter_by(school_id=current_school_id).scalar() or 0
    today_expenditure = db.session.query(db.func.sum(Expenditure.amount_paid)).filter_by(school_id=current_school_id, date=today).scalar() or 0
    
    today_income = total_pta_income + total_sdf_income + total_boarding_income + total_other_income
    today_net = today_income - today_expenditure
    
    # Get recent transactions (school-filtered) - include all other income
    recent_income = Income.query.filter_by(school_id=current_school_id).order_by(Income.id.desc()).limit(5).all()
    recent_other_income = OtherIncome.query.filter_by(school_id=current_school_id).order_by(OtherIncome.id.desc()).limit(5).all()
    recent_expenditure = Expenditure.query.filter_by(school_id=current_school_id, date=today).order_by(Expenditure.id.desc()).limit(5).all()
    
    transactions = []
    
    # Add student income transactions
    processed_students = set()
    for income in recent_income:
        student = Student.query.filter_by(student_id=income.student_id).first()
        if student and income.student_id not in processed_students:
            total_paid = student.pta_amount_paid + student.sdf_amount_paid + student.boarding_amount_paid
            if total_paid > 0:
                transactions.append({
                    'time': income.payment_date.strftime('%H:%M') if hasattr(income.payment_date, 'strftime') else 'N/A',
                    'type': 'Income',
                    'description': f'{student.name if student else income.student_id} - Student Payment',
                    'amount': f'{total_paid:.2f}'
                })
                processed_students.add(income.student_id)
    
    # Add other income transactions
    for other_income in recent_other_income:
        transactions.append({
            'time': other_income.date.strftime('%H:%M') if hasattr(other_income.date, 'strftime') else 'N/A',
            'type': 'Income',
            'description': f'{other_income.customer_name} - {other_income.income_type}',
            'amount': f'{other_income.amount_paid:.2f}'
        })
    
    # Add expenditure transactions
    for expenditure in recent_expenditure:
        transactions.append({
            'time': expenditure.date.strftime('%H:%M') if hasattr(expenditure.date, 'strftime') else 'N/A',
            'type': 'Expenditure', 
            'description': expenditure.activity_service,
            'amount': f'{expenditure.amount_paid:.2f}'
        })
    
    # Sort transactions by time (most recent first)
    transactions.sort(key=lambda x: x['time'], reverse=True)
    
    return jsonify({
        'income': f'{today_income:.2f}',
        'expenditure': f'{today_expenditure:.2f}',
        'net': f'{today_net:.2f}',
        'transactions': transactions[:5],  # Limit to 5 most recent to avoid clutter
        'income_hidden': '****',
        'net_hidden': '****'
    })

@app.route('/school_config', methods=['GET', 'POST'])
@login_required
def school_config():
    """Manage school configuration including school name"""
    if request.method == 'POST':
        try:
            school_name = request.form['school_name']
            school_address = request.form.get('school_address', '')
            head_teacher_contact = request.form.get('head_teacher_contact', '')
            bursar_contact = request.form.get('bursar_contact', '')
            school_email = request.form.get('school_email', '')
            
            # Update existing configuration instead of creating new one
            current_config = SchoolConfiguration.query.filter_by(is_active=True).first()
            if current_config:
                current_config.school_name = school_name
                current_config.school_address = school_address
                current_config.head_teacher_contact = head_teacher_contact
                current_config.bursar_contact = bursar_contact
                current_config.school_email = school_email
                current_config.updated_at = datetime.utcnow()
            else:
                # Create new configuration if none exists
                current_config = SchoolConfiguration(
                    school_name=school_name,
                    school_address=school_address,
                    head_teacher_contact=head_teacher_contact,
                    bursar_contact=bursar_contact,
                    school_email=school_email,
                    is_active=True
                )
                db.session.add(current_config)
            
            db.session.commit()
            flash('School configuration updated successfully!', 'success')
            return redirect(url_for('school_config'))
        except Exception as e:
            flash(f'Error updating school configuration: {str(e)}', 'error')
    # Get current configuration
    current_config = SchoolConfiguration.query.filter_by(is_active=True).first()
    if not current_config:
        # Create default configuration if none exists
        current_config = SchoolConfiguration(
            school_name='SmartFee Revenue Collection System',
            is_active=True
        )
        db.session.add(current_config)
        db.session.commit()
    return render_template('school_config.html', current_config=current_config)

@app.route('/developer_settings', methods=['GET', 'POST'])
@login_required
def developer_settings():
    """Developer-only settings for changing username and password"""
    # Special access check - only allow if user knows the developer key
    if request.method == 'GET' and 'dev_access' not in request.args:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Verify developer access key
        dev_key = request.form.get('dev_key')
        expected_dev_key = os.environ.get('DEVELOPER_ACCESS_KEY')
        if not expected_dev_key or dev_key != expected_dev_key:
            flash('Invalid developer access key!', 'error')
            return redirect(url_for('index'))
        
        try:
            new_username = request.form['new_username']
            new_password = request.form['new_password']
            confirm_password = request.form['confirm_password']
            
            if new_password != confirm_password:
                flash('Passwords do not match!', 'error')
                return render_template('developer_settings.html')
            
            # Check if user already exists
            existing_user = User.query.filter_by(username=new_username).first()
            
            if existing_user:
                # Update existing user
                existing_user.password = new_password
                existing_user.updated_at = datetime.utcnow()
            else:
                # Create new user
                new_user = User(
                    username=new_username,
                    password=new_password,
                    role='admin'
                )
                db.session.add(new_user)
            
            db.session.commit()
            flash('Credentials updated successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Error updating credentials: {str(e)}', 'error')
    
    return render_template('developer_settings.html')

@app.route('/delete_expenditure/<int:expenditure_id>', methods=['POST'])
@login_required
def delete_expenditure(expenditure_id):
    """Delete an expenditure record"""
    try:
        # Ensure expenditure belongs to current school
        expenditure_query = get_school_filtered_query(Expenditure)
        expenditure = expenditure_query.filter_by(id=expenditure_id).first_or_404()
        db.session.delete(expenditure)
        db.session.commit()
        flash('Expenditure record deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting expenditure record: {str(e)}', 'error')
    return redirect(url_for('expenditure'))

@app.route('/edit_expenditure/<int:expenditure_id>', methods=['GET', 'POST'])
@login_required
def edit_expenditure(expenditure_id):
    """Edit an expenditure record"""
    # Ensure expenditure belongs to current school
    expenditure_query = get_school_filtered_query(Expenditure)
    expenditure = expenditure_query.filter_by(id=expenditure_id).first_or_404()
    
    if request.method == 'POST':
        try:
            expenditure.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
            expenditure.activity_service = request.form['activity_service']
            expenditure.voucher_no = request.form['voucher_no']
            expenditure.cheque_no = request.form['cheque_no']
            expenditure.amount_paid = float(request.form['amount_paid'])
            expenditure.fund_type = request.form['fund_type']
            
            db.session.commit()
            flash('Expenditure record updated successfully!', 'success')
            return redirect(url_for('expenditure'))
        except Exception as e:
            flash(f'Error updating expenditure record: {str(e)}', 'error')
    
    return render_template('edit_expenditure.html', expenditure=expenditure)

@app.route('/delete_student/<int:student_id>', methods=['POST'])
@login_required
def delete_student(student_id):
    """Delete a student record with enhanced tenant isolation"""
    try:
        # Enhanced tenant isolation check
        current_school_id = get_current_school_id()
        if not current_school_id and session.get('user_role') != 'developer':
            flash('Access denied. No school context.', 'error')
            return redirect(url_for('students'))
        
        # Check if student exists and belongs to current school
        student_query = get_school_filtered_query(Student)
        student = student_query.filter_by(id=student_id).first()
        if not student:
            flash(f'Student with ID {student_id} not found or access denied!', 'error')
            return redirect(url_for('students'))
        
        # Double-check school ownership
        if student.school_id != current_school_id and session.get('user_role') != 'developer':
            flash('Access denied. Student belongs to different school.', 'error')
            return redirect(url_for('students'))
        
        # Store student info for confirmation message
        student_name = student.name
        student_id_number = student.student_id
        
        # Delete related income records first (school-filtered)
        income_query = get_school_filtered_query(Income)
        income_records = income_query.filter_by(student_id=student.student_id).all()
        for income in income_records:
            db.session.delete(income)
        
        # Delete the student record
        db.session.delete(student)
        db.session.commit()
        
        flash(f'Student "{student_name}" (ID: {student_id_number}) and all related payment records deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting student record: {str(e)}. Please ensure no other records depend on this student.', 'error')
    return redirect(url_for('students'))

@app.route('/api/check_student_id/<student_id>')
@login_required
def check_student_id(student_id):
    """Check if a student ID is available in current school"""
    # Check within current school only
    student_query = get_school_filtered_query(Student)
    existing_student = student_query.filter_by(student_id=student_id).first()
    return jsonify({'available': existing_student is None})

@app.route('/debug_deposit_slips_page')
@login_required
def debug_deposit_slips_page():
    """Debug page to check and fix deposit slip references"""
    if session.get('user_role') != 'developer':
        flash('Access denied. Developer privileges required.', 'error')
        return redirect(url_for('index'))
    
    return render_template('debug_deposit_slips.html')

@app.route('/debug_deposit_slips')
@login_required
def debug_deposit_slips():
    """Debug route to check deposit slip references in the database"""
    if session.get('user_role') != 'developer':
        flash('Access denied. Developer privileges required.', 'error')
        return redirect(url_for('index'))
    
    current_school_id = get_current_school_id()
    
    # Get all income records
    income_query = get_school_filtered_query(Income) if current_school_id else Income.query
    income_records = income_query.order_by(Income.payment_date.desc()).limit(20).all()
    
    debug_data = []
    for income in income_records:
        # Try to decrypt if encrypted
        if income.school and income.school.encryption_key and income.payment_reference:
            try:
                decrypted_ref = decrypt_sensitive_field(income.payment_reference, income.school_id, income.school.encryption_key)
            except:
                decrypted_ref = f"DECRYPT_ERROR: {income.payment_reference[:20]}..."
        else:
            decrypted_ref = income.payment_reference or "NULL"
        
        debug_data.append({
            'id': income.id,
            'student_id': income.student_id,
            'payment_date': income.payment_date.strftime('%Y-%m-%d') if income.payment_date else None,
            'raw_reference': income.payment_reference,
            'decrypted_reference': decrypted_ref,
            'school_id': income.school_id
        })
    
    return jsonify({
        'total_records': len(debug_data),
        'records': debug_data
    })



@app.route('/budget')
@login_required
def budget():
    # Developers should not see school data
    if session.get('user_role') == 'developer':
        flash('Access denied. Developers cannot view school data.', 'error')
        return redirect(url_for('manage_schools'))
    
    current_school_id = get_current_school_id()
    if not current_school_id:
        flash('No school access configured. Please contact administrator.', 'error')
        return redirect(url_for('index'))
    
    try:
        # Ensure Budget table exists
        db.create_all()
        
        # Get school-filtered budget items
        budget_query = get_school_filtered_query(Budget)
        budget_items = budget_query.order_by(Budget.id).all()
        
        # If no budget items exist, create them from expenditure records (school-specific)
        if not budget_items:
            expenditure_query = get_school_filtered_query(Expenditure)
            activities = expenditure_query.with_entities(Expenditure.activity_service).distinct().all()
            for activity in activities:
                budget_item = Budget(
                    school_id=current_school_id,
                    activity_service=activity[0], 
                    proposed_allocation=0.0
                )
                db.session.add(budget_item)
            db.session.commit()
            budget_items = budget_query.order_by(Budget.activity_service).all()
        
        # Calculate totals (school-filtered)
        total_budget = sum(item.proposed_allocation for item in budget_items)
        pta_income = db.session.query(db.func.sum(Student.pta_amount_paid)).filter_by(school_id=current_school_id).scalar() or 0
        sdf_income = db.session.query(db.func.sum(Student.sdf_amount_paid)).filter_by(school_id=current_school_id).scalar() or 0
        boarding_income = db.session.query(db.func.sum(Student.boarding_amount_paid)).filter_by(school_id=current_school_id).scalar() or 0
        other_income = db.session.query(db.func.sum(OtherIncome.amount_paid)).filter_by(school_id=current_school_id).scalar() or 0
        total_income = pta_income + sdf_income + boarding_income + other_income
        
        # Calculate actual spending per activity
        spending_data = []
        for item in budget_items:
            if item.is_category:
                spending_data.append({
                    'activity': item.activity_service,
                    'budgeted': 0,
                    'spent': 0,
                    'balance': 0,
                    'is_category': True
                })
            else:
                spent = db.session.query(db.func.sum(Expenditure.amount_paid)).filter_by(school_id=current_school_id, activity_service=item.activity_service).scalar() or 0
                balance = item.proposed_allocation - spent
                spending_data.append({
                    'activity': item.activity_service,
                    'budgeted': item.proposed_allocation,
                    'spent': spent,
                    'balance': balance,
                    'is_category': False
                })
        
        # Predefined activities/services list from expenditure categories
        predefined_activities = [
            # (A). Facilitating Office Operations
            '1203 - Public Transport',
            '1401 - Heating and Lighting',
            '1402 - Telephone Charges',
            '1405 - Water and Sanitation',
            '1502 - Consumable Stores',
            '1504 - Postage',
            '1505 - Printing Cost',
            '1406 - Publication and Advertisement',
            '1506 - Stationery',
            '1507 - Uniform and Protective Wear',
            '2401 - Fuel and Lubricants',
            '2321 - Subscriptions',
            '0251 - Purchase of Plant and Office Equipment',
            # (B). Management of School Based and National Examinations
            '1803 - Examinations',
            '1204 - Subsistence Allowance',
            # (C). SMASSE
            # (D). Sporting Activities
            '1805 - Sporting Equipment',
            # (E). Support to SNE
            '1806 - Purchase of Special Needs Materials',
            # (F). Procurement of Teaching and Learning Materials
            '1807 - Science Consumables',
            '1804 - Text Books',
            '1808 - Purchase of School Supplies',
            '1614 - HIV/AIDS Services',
            '1601 - Drugs',
            # (G). Maintenance of Infrastructure
            '2501 - Maintenance of Buildings',
            '2504 - Maintenance of Water Supplies',
            # (H). COSOMA & Computer Service Subscription
            # (I). In-service Training for Teachers
            # (J). Processing of Payment Vouchers
            # (K). Provision of Sanitary Pads to Girls in Secondary Schools
            # (L). Provision of PPEs to Schools
            # (M). Provision of Food and Other Boarding Necessities to Learners
            '1801 - Boarding Expenses'
        ]
        
        return render_template('budget.html', 
                             budget_items=budget_items,
                             total_budget=total_budget,
                             total_income=total_income,
                             pta_income=pta_income,
                             sdf_income=sdf_income,
                             boarding_income=boarding_income,
                             other_income=other_income,
                             spending_data=spending_data,
                             predefined_activities=predefined_activities)
    except Exception as e:
        flash(f'Error loading budget: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/update_budget', methods=['POST'])
@login_required
def update_budget():
    try:
        # Ensure Budget table exists
        db.create_all()
        
        for key, value in request.form.items():
            if key.startswith('allocation_'):
                budget_id = int(key.replace('allocation_', ''))
                allocation = float(value) if value else 0.0
                budget_item = Budget.query.get(budget_id)
                if budget_item:
                    budget_item.proposed_allocation = allocation
        
        db.session.commit()
        flash('Budget updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating budget: {str(e)}', 'error')
    
    return redirect(url_for('budget'))

@app.route('/add_budget_item', methods=['POST'])
@login_required
def add_budget_item():
    current_school_id = get_current_school_id()
    if not current_school_id:
        flash('No school access configured. Please contact administrator.', 'error')
        return redirect(url_for('budget'))
    
    try:
        activity_service = request.form['activity_service']
        proposed_allocation = float(request.form.get('proposed_allocation', 0.0))
        
        budget_item = Budget(
            school_id=current_school_id,
            activity_service=activity_service,
            proposed_allocation=proposed_allocation
        )
        db.session.add(budget_item)
        db.session.commit()
        flash('Budget item added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding budget item: {str(e)}', 'error')
    
    return redirect(url_for('budget'))

@app.route('/delete_budget_item/<int:item_id>', methods=['POST'])
@login_required
def delete_budget_item(item_id):
    current_school_id = get_current_school_id()
    if not current_school_id:
        flash('No school access configured. Please contact administrator.', 'error')
        return redirect(url_for('budget'))
    
    try:
        # Ensure budget item belongs to current school
        budget_query = get_school_filtered_query(Budget)
        budget_item = budget_query.filter_by(id=item_id).first()
        
        if not budget_item:
            flash('Budget item not found!', 'error')
            return redirect(url_for('budget'))
        
        activity_name = budget_item.activity_service
        db.session.delete(budget_item)
        db.session.commit()
        flash(f'Budget item "{activity_name}" deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting budget item: {str(e)}', 'error')
    
    return redirect(url_for('budget'))


# Combined PTA/SDF receipt for a student
# Remove old combined receipt route - replaced by professional receipt
# @app.route('/print_receipt_combined/<student_id>') - REMOVED



@app.route('/download_search_results')
@login_required
def download_search_results():
    from fpdf2 import FPDF
    import io

    # Get search parameters
    student_name = request.args.get('student_name', '').strip()
    form_class = request.args.get('form_class', '').strip()
    deposit_ref = request.args.get('deposit_ref', '').strip()

    # Get school context
    current_school_id = get_current_school_id()
    if not current_school_id:
        return 'Access denied', 403

    # Get all income records
    income_query = get_school_filtered_query(Income)
    income_records = income_query.all()

    # Filter based on search criteria
    filtered_records = []
    for record in income_records:
        record_name = record.student_name.lower() if record.student_name else ''
        record_class = record.form_class.lower() if record.form_class else ''
        record_ref = record.deposit_ref_no.lower() if record.deposit_ref_no else ''

        matches = True
        if student_name and student_name.lower() not in record_name:
            matches = False
        if form_class and form_class.lower() not in record_class:
            matches = False
        if deposit_ref and deposit_ref.lower() not in record_ref:
            matches = False

        if matches:
            filtered_records.append(record)

    # Create PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    
    # Add title and search parameters
    pdf.cell(0, 10, 'Payment Records - Search Results', 0, 1, 'C')
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 6, f'Student Name: {student_name or "All"}', 0, 1)
    pdf.cell(0, 6, f'Class/Form: {form_class or "All"}', 0, 1)
    pdf.cell(0, 6, f'Deposit Ref: {deposit_ref or "All"}', 0, 1)
    pdf.ln(10)

    # Add table headers
    pdf.set_font('Arial', 'B', 8)
    col_widths = [20, 25, 40, 25, 25, 25, 30]
    headers = ['Date', 'Student ID', 'Name', 'Class', 'PTA Paid', 'SDF Paid', 'Boarding Paid']
    
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 7, header, 1)
    pdf.ln()

    # Add data rows
    pdf.set_font('Arial', '', 8)
    for record in filtered_records:
        pdf.cell(col_widths[0], 6, record.payment_date.strftime('%Y-%m-%d') if record.payment_date else 'N/A', 1)
        pdf.cell(col_widths[1], 6, record.student_id or 'N/A', 1)
        pdf.cell(col_widths[2], 6, record.student_name or 'N/A', 1)
        pdf.cell(col_widths[3], 6, record.form_class or 'N/A', 1)
        pdf.cell(col_widths[4], 6, f'MK {record.pta_amount:,.2f}' if record.pta_amount else 'MK 0.00', 1)
        pdf.cell(col_widths[5], 6, f'MK {record.sdf_amount:,.2f}' if record.sdf_amount else 'MK 0.00', 1)
        pdf.cell(col_widths[6], 6, f'MK {record.boarding_amount:,.2f}' if record.boarding_amount else 'MK 0.00', 1)
        pdf.ln()

    # Get PDF as bytes and wrap in BytesIO
    pdf_buffer = io.BytesIO(pdf.output(dest='S'))
    pdf_buffer.seek(0)

    # Get school name for filename
    school = SchoolConfiguration.query.get(current_school_id)
    school_name = school.school_name if school else 'school'
    filename = f"{school_name}_payment_records.pdf".replace(' ', '_')

    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )

# SMS Notification Routes
@app.route('/sms_notifications')
@login_required
def sms_notifications():
    # Get school-filtered students with outstanding balances
    student_query = get_school_filtered_query(Student)
    students = student_query.all()
    students_with_balances = []
    students_with_phones = []
    
    for student in students:
        pta_balance = student.get_pta_balance()
        sdf_balance = student.get_sdf_balance()
        boarding_balance = student.get_boarding_balance()
        total_balance = pta_balance + sdf_balance + boarding_balance
        
        if total_balance > 0:
            student_data = {
                'student': student,
                'pta_balance': pta_balance,
                'sdf_balance': sdf_balance,
                'boarding_balance': boarding_balance,
                'total_balance': total_balance
            }
            students_with_balances.append(student_data)
            
            if student.parent_phone:
                students_with_phones.append(student_data)
    
    # Count SMS sent today (placeholder - would need SMS log table)
    sms_sent_today = 0
    
    return render_template('sms_notifications.html', 
                         students_with_balances=students_with_balances,
                         students_with_phones=students_with_phones,
                         sms_sent_today=sms_sent_today)

@app.route('/send_bulk_sms_reminders', methods=['POST'])
@login_required
@csrf.exempt
def send_bulk_sms_reminders():
    try:
        print("DEBUG: send_bulk_sms_reminders route called")
        print(f"DEBUG: Request method: {request.method}")
        print(f"DEBUG: Request headers: {dict(request.headers)}")
        print(f"DEBUG: Request data: {request.get_data()}")
        # Get school-filtered students with balances and phone numbers
        student_query = get_school_filtered_query(Student)
        students = student_query.all()
        students_to_notify = []
        
        for student in students:
            total_balance = student.get_pta_balance() + student.get_sdf_balance() + student.get_boarding_balance()
            if total_balance > 0 and student.parent_phone:
                students_to_notify.append({
                    'student': student,
                    'parent_phone': student.parent_phone
                })
        
        if not students_to_notify:
            return jsonify({'success': False, 'error': 'No students with balances and phone numbers found'})
        
        # Send bulk SMS
        results = sms_service.send_bulk_reminders(students_to_notify)
        
        sent_count = sum(1 for r in results if r['success'])
        failed_count = len(results) - sent_count
        
        return jsonify({
            'success': True,
            'sent_count': sent_count,
            'failed_count': failed_count,
            'results': results
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/send_single_sms_reminder/<student_id>', methods=['POST'])
@login_required
@csrf.exempt
def send_single_sms_reminder(student_id):
    try:
        print(f"DEBUG: send_single_sms_reminder called for student_id: {student_id}")
        print(f"DEBUG: Request method: {request.method}")
        print(f"DEBUG: Request headers: {dict(request.headers)}")
        print(f"DEBUG: Request data: {request.get_data()}")
        
        # Get school-filtered student
        student_query = get_school_filtered_query(Student)
        student = student_query.filter_by(student_id=student_id).first()
        print(f"DEBUG: Student found: {student is not None}")
        if not student:
            print("DEBUG: Student not found, returning error")
            return jsonify({'success': False, 'error': 'Student not found'})
        
        if not student.parent_phone:
            return jsonify({'success': False, 'error': 'No parent phone number'})
        
        total_balance = student.get_pta_balance() + student.get_sdf_balance() + student.get_boarding_balance()
        if total_balance <= 0:
            return jsonify({'success': False, 'error': 'No outstanding balance'})
        
        result = sms_service.send_balance_reminder(student, student.parent_phone)
        return jsonify(result)
        
    except Exception as e:
        print(f"DEBUG: Exception in send_single_sms_reminder: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/print_income')
@login_required
def print_income():
    current_school_id = get_current_school_id()
    if not current_school_id and session.get('user_role') != 'developer':
        flash('No school access configured. Please contact administrator.', 'error')
        return redirect(url_for('index'))
    
    # Get school-filtered students
    student_query = get_school_filtered_query(Student)
    all_students = student_query.all()
    
    # Calculate totals
    pta_total = db.session.query(db.func.sum(Student.pta_amount_paid)).filter_by(school_id=current_school_id).scalar() or 0
    sdf_total = db.session.query(db.func.sum(Student.sdf_amount_paid)).filter_by(school_id=current_school_id).scalar() or 0
    boarding_total = db.session.query(db.func.sum(Student.boarding_amount_paid)).filter_by(school_id=current_school_id).scalar() or 0
    other_income_total = db.session.query(db.func.sum(OtherIncome.amount_paid)).filter_by(school_id=current_school_id).scalar() or 0
    
    # Prepare student records
    student_records = []
    for student in all_students:
        decrypted_data = decrypt_student_data(student)
        student_records.append({
            'student_id': decrypted_data['student_id'],
            'student_name': decrypted_data['name'],
            'form_class': decrypted_data['form_class'],
            'pta_paid': student.pta_amount_paid,
            'sdf_paid': student.sdf_amount_paid,
            'boarding_paid': student.boarding_amount_paid
        })
    
    return render_template('print_income.html',
                         student_records=student_records,
                         pta_total=pta_total,
                         sdf_total=sdf_total,
                         boarding_total=boarding_total,
                         other_income_total=other_income_total,
                         grand_total=pta_total + sdf_total + boarding_total + other_income_total)

@app.route('/print_students')
@login_required
def print_students():
    current_school_id = get_current_school_id()
    if not current_school_id and session.get('user_role') != 'developer':
        flash('No school access configured. Please contact administrator.', 'error')
        return redirect(url_for('index'))
    
    # Get school-filtered students
    student_query = get_school_filtered_query(Student)
    all_students = student_query.all()
    
    # Decrypt student data and prepare for printing
    students_data = []
    for student in all_students:
        decrypted_data = decrypt_student_data(student)
        students_data.append({
            'student_id': decrypted_data['student_id'],
            'name': decrypted_data['name'],
            'sex': decrypted_data['sex'],
            'form_class': decrypted_data['form_class'],
            'parent_phone': decrypted_data['parent_phone'],
            'pta_paid': student.pta_amount_paid,
            'sdf_paid': student.sdf_amount_paid,
            'boarding_paid': student.boarding_amount_paid,
            'is_paid_in_full': student.is_paid_in_full()
        })
    
    # Sort by student ID
    students_data.sort(key=lambda x: int(x['student_id']) if x['student_id'].isdigit() else 9999)
    
    return render_template('print_students.html', students=students_data)

@app.route('/print_expenditure')
@login_required
def print_expenditure():
    current_school_id = get_current_school_id()
    if not current_school_id and session.get('user_role') != 'developer':
        flash('No school access configured. Please contact administrator.', 'error')
        return redirect(url_for('index'))
    
    # Get school-filtered expenditures
    expenditure_query = get_school_filtered_query(Expenditure)
    expenditures = expenditure_query.order_by(Expenditure.date.desc()).all()
    
    # Calculate totals by fund type
    pta_expenditure = db.session.query(db.func.sum(Expenditure.amount_paid)).filter_by(school_id=current_school_id, fund_type='PTA').scalar() or 0
    sdf_expenditure = db.session.query(db.func.sum(Expenditure.amount_paid)).filter_by(school_id=current_school_id, fund_type='SDF').scalar() or 0
    boarding_expenditure = db.session.query(db.func.sum(Expenditure.amount_paid)).filter_by(school_id=current_school_id, fund_type='Boarding').scalar() or 0
    other_expenditure = db.session.query(db.func.sum(Expenditure.amount_paid)).filter_by(school_id=current_school_id, fund_type='Other Income').scalar() or 0
    
    return render_template('print_expenditure.html',
                         expenditures=expenditures,
                         pta_expenditure=pta_expenditure,
                         sdf_expenditure=sdf_expenditure,
                         boarding_expenditure=boarding_expenditure,
                         other_expenditure=other_expenditure,
                         total_expenditure=pta_expenditure + sdf_expenditure + boarding_expenditure + other_expenditure)

@app.route('/update_sms_config', methods=['POST'])
@login_required
def update_sms_config():
    try:
        # Update environment variables (in production, these should be stored securely)
        api_username = request.form['api_username']
        api_key = request.form['api_key']
        sender_id = request.form['sender_id']
        
        # For now, just flash a message. In production, you'd want to store these securely
        flash(f'SMS configuration updated! Please set environment variables: AFRICASTALKING_USERNAME={api_username}, AFRICASTALKING_API_KEY=*****, SMS_SENDER_ID={sender_id}', 'info')
        
        return redirect(url_for('sms_notifications'))
        
    except Exception as e:
        flash(f'Error updating SMS configuration: {str(e)}', 'error')
        return redirect(url_for('sms_notifications'))

@app.route('/test_sms')
@login_required
def test_sms():
    return render_template('test_sms.html')

@app.route('/test_sms_send', methods=['POST'])
@login_required
def test_sms_send():
    try:
        phone_number = request.form['phone_number']
        message = request.form['message']
        
        result = sms_service.send_sms(phone_number, message)
        
        return render_template('test_sms.html', 
                             test_result=result, 
                             test_phone=phone_number)
        
    except Exception as e:
        return render_template('test_sms.html', 
                             test_result={'success': False, 'error': str(e)}, 
                             test_phone=request.form.get('phone_number', ''))

# Debug route for checking deposit slip references
@app.route('/fix_missing_references', methods=['POST'])
@login_required
def fix_missing_references():
    """Fix missing payment references in Income and Receipt records"""
    if session.get('user_role') != 'developer':
        return jsonify({'success': False, 'error': 'Access denied'})
    
    try:
        fixed_income = 0
        fixed_receipts = 0
        
        # Fix Income records
        income_records = Income.query.filter(
            (Income.payment_reference == None) | (Income.payment_reference == '')
        ).all()
        
        for income in income_records:
            default_ref = f"REF{income.id:06d}"
            if income.school and income.school.encryption_key:
                income.payment_reference = encrypt_sensitive_field(default_ref, income.school_id, income.school.encryption_key)
            else:
                income.payment_reference = default_ref
            fixed_income += 1
        
        # Fix Receipt records
        receipt_records = Receipt.query.filter(
            (Receipt.deposit_slip_ref == None) | (Receipt.deposit_slip_ref == '')
        ).all()
        
        for receipt in receipt_records:
            default_ref = f"REF{receipt.id:06d}"
            if receipt.school and receipt.school.encryption_key:
                receipt.deposit_slip_ref = encrypt_sensitive_field(default_ref, receipt.school_id, receipt.school.encryption_key)
            else:
                receipt.deposit_slip_ref = default_ref
            fixed_receipts += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'fixed_income': fixed_income,
            'fixed_receipts': fixed_receipts,
            'message': f'Fixed {fixed_income} income and {fixed_receipts} receipt records'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/fix_deposit_slips', methods=['POST'])
@login_required
def fix_deposit_slips():
    """Legacy route - redirects to fix_missing_references"""
    return fix_missing_references()

if __name__ == '__main__':
    with app.app_context():
        # Create database tables
        db.create_all()
        
        # Ensure database schema is up to date
        ensure_database_schema()
        
        # Create a default user if the database is empty
        create_default_school_and_admin()
    
    # This block is for local development only.
    # In production, a WSGI server like Gunicorn (specified in the Procfile) is used.
    print("\n" + "="*50)
    print("Starting local development server...")
    print("Access the system at: http://127.0.0.1:5001")
    print("="*50 + "\n")
    app.run(host='127.0.0.1', port=5001, debug=True)
