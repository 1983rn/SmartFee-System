"""
Data isolation helpers used across the app.
For this run, tenant restrictions are relaxed (single-tenant/no-tenant mode)
so helpers default to permissive behavior while keeping the same API.
"""

from typing import Any, Dict
from flask import session
from encryption_utils import (
    encrypt_sensitive_field,
    decrypt_sensitive_field,
    encrypt_phone_field,
    decrypt_phone_field,
)


def get_current_school_id() -> int | None:
    """Return current school_id from session if set.
    In no-tenant mode this may be None, which is acceptable for developer role.
    """
    return session.get("school_id")


def ensure_school_access(school_id: int | None = None) -> bool:
    """Ensure user has access to the specified school data with enhanced security."""
    # Developers have global access
    if session.get("user_role") == "developer":
        return True

    current_school_id = session.get("school_id")
    
    # School admins must have a school_id in session
    if not current_school_id:
        return False
    
    # If a specific school is requested, it must match the session school_id
    if school_id is not None:
        return current_school_id == school_id
    
    # Validate that the school is still active and not blocked
    try:
        from app import SchoolConfiguration
        school = SchoolConfiguration.query.get(current_school_id)
        if not school or not school.is_active or school.is_blocked:
            return False
    except Exception:
        return False
    
    return True


def get_school_filtered_query(model_class):
    """Return a query for the given model with enhanced tenant isolation.
    Developers cannot see school data. School admins only see their school's data.
    """
    try:
        # Developers cannot see school data - return empty query
        if session.get("user_role") == "developer":
            return model_class.query.filter(model_class.id == -1)  # Impossible condition

        current_school_id = session.get("school_id")
        
        # School admins must have a school_id and model must support school_id
        if not current_school_id:
            # Return empty query for security - no school context means no data access
            return model_class.query.filter(model_class.id == -1)  # Impossible condition
        
        if hasattr(model_class, "school_id"):
            # Validate school access before returning filtered query
            if ensure_school_access(current_school_id):
                return model_class.query.filter_by(school_id=current_school_id)
            else:
                # School access denied - return empty query
                return model_class.query.filter(model_class.id == -1)
        
        # Model doesn't have school_id - return empty query for security
        return model_class.query.filter(model_class.id == -1)
        
    except Exception:
        # If anything goes wrong, return empty query for security
        return model_class.query.filter(model_class.id == -1)


def decrypt_student_data(student: Any) -> Dict[str, Any]:
    """Return a dict of display-ready student fields. If the student's
    school has an encryption key, attempt decryption; otherwise return as-is.
    """
    school_id = getattr(student, "school_id", None)
    encryption_key = getattr(getattr(student, "school", None), "encryption_key", None)

    if not encryption_key:
        return {
            "student_id": getattr(student, "student_id", None),
            "name": getattr(student, "name", None),
            "sex": getattr(student, "sex", None),
            "form_class": getattr(student, "form_class", None),
            "parent_phone": getattr(student, "parent_phone", None),
        }

    return {
        "student_id": decrypt_sensitive_field(student.student_id, school_id, encryption_key)
        if getattr(student, "student_id", None) is not None
        else None,
        "name": decrypt_sensitive_field(student.name, school_id, encryption_key)
        if getattr(student, "name", None) is not None
        else None,
        "sex": decrypt_sensitive_field(student.sex, school_id, encryption_key)
        if getattr(student, "sex", None) is not None
        else None,
        "form_class": decrypt_sensitive_field(student.form_class, school_id, encryption_key)
        if getattr(student, "form_class", None) is not None
        else None,
        "parent_phone": decrypt_phone_field(student.parent_phone, school_id, encryption_key)
        if getattr(student, "parent_phone", None) is not None
        else None,
    }
