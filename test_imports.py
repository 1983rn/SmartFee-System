#!/usr/bin/env python3
"""
Test script to check if all imports work correctly
"""

print("Testing imports...")

try:
    print("1. Testing Flask imports...")
    from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
    from flask_sqlalchemy import SQLAlchemy
    from flask_wtf.csrf import CSRFProtect
    print("   ✓ Flask imports successful")
except ImportError as e:
    print(f"   ✗ Flask import error: {e}")
    exit(1)

try:
    print("2. Testing datetime imports...")
    from datetime import datetime, timedelta
    from datetime import datetime as dt
    print("   ✓ Datetime imports successful")
except ImportError as e:
    print(f"   ✗ Datetime import error: {e}")
    exit(1)

try:
    print("3. Testing other standard library imports...")
    from functools import wraps
    import os
    print("   ✓ Standard library imports successful")
except ImportError as e:
    print(f"   ✗ Standard library import error: {e}")
    exit(1)

try:
    print("4. Testing dotenv import...")
    from dotenv import load_dotenv
    print("   ✓ Dotenv import successful")
except ImportError as e:
    print(f"   ✗ Dotenv import error: {e}")
    exit(1)

try:
    print("5. Testing custom module imports...")
    from sms_service import sms_service
    print("   ✓ SMS service import successful")
except ImportError as e:
    print(f"   ✗ SMS service import error: {e}")

try:
    from encryption_utils import school_encryption, encrypt_sensitive_field, decrypt_sensitive_field, encrypt_phone_field, decrypt_phone_field
    print("   ✓ Encryption utils import successful")
except ImportError as e:
    print(f"   ✗ Encryption utils import error: {e}")

try:
    from data_isolation_helpers import get_current_school_id, ensure_school_access, get_school_filtered_query, decrypt_student_data
    print("   ✓ Data isolation helpers import successful")
except ImportError as e:
    print(f"   ✗ Data isolation helpers import error: {e}")

try:
    from tenant_enforcement import tenant_manager, tenant_required, TenantEnforcementMixin, validate_tenant_access
    print("   ✓ Tenant enforcement import successful")
except ImportError as e:
    print(f"   ✗ Tenant enforcement import error: {e}")

try:
    from core_models import create_core_models
    print("   ✓ Core models import successful")
except ImportError as e:
    print(f"   ✗ Core models import error: {e}")

print("\nAll critical imports tested!")
print("If you see this message, the basic imports are working.")
print("The application should be able to start now.")