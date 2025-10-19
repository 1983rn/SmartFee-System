"""
Tenant enforcement system for Single Database, Separate Schemas approach
"""

from flask import session, g, has_request_context
from sqlalchemy import event
from sqlalchemy.orm import Query
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class TenantEnforcementMixin:
    """Mixin to add automatic tenant enforcement to models"""
    
    @classmethod
    def __declare_last__(cls):
        """Called after all model attributes are configured"""
        if hasattr(cls, 'school_id'):
            event.listen(cls, 'before_insert', cls._inject_tenant_id)
            event.listen(cls, 'before_update', cls._validate_tenant_access)
    
    @staticmethod
    def _inject_tenant_id(mapper, connection, target):
        """Automatically inject school_id for new records"""
        if hasattr(target, 'school_id') and target.school_id is None:
            if has_request_context():
                current_school_id = session.get('school_id')
                if current_school_id:
                    target.school_id = current_school_id
    
    @staticmethod
    def _validate_tenant_access(mapper, connection, target):
        """Validate tenant access on updates"""
        if hasattr(target, 'school_id') and has_request_context():
            current_school_id = session.get('school_id')
            user_role = session.get('user_role')
            
            if user_role == 'developer':
                return
            
            if current_school_id and target.school_id != current_school_id:
                raise ValueError(f"Access denied: Cannot modify record from school {target.school_id}")

class TenantAwareQuery(Query):
    """Custom query class that automatically filters by tenant"""
    
    def __init__(self, entities, session=None):
        super().__init__(entities, session)
        self._auto_tenant_filter = True
    
    def filter_by_tenant(self):
        """Apply tenant filtering if not already applied"""
        if not hasattr(self, '_tenant_filtered'):
            try:
                if not has_request_context():
                    self._tenant_filtered = True
                    return self
                
                current_school_id = session.get('school_id')
                user_role = session.get('user_role')
                
                if user_role == 'developer':
                    self._tenant_filtered = True
                    return self
                
                if current_school_id and hasattr(self.column_descriptions[0]['entity'], 'school_id'):
                    self = self.filter_by(school_id=current_school_id)
                    self._tenant_filtered = True
            except Exception as e:
                logger.debug(f"Tenant filtering skipped: {e}")
            
            self._tenant_filtered = True
        
        return self
    
    def all(self):
        """Override all() to apply tenant filtering"""
        return self.filter_by_tenant().all()
    
    def first(self):
        """Override first() to apply tenant filtering"""
        return self.filter_by_tenant().first()
    
    def count(self):
        """Override count() to apply tenant filtering"""
        return self.filter_by_tenant().count()

def tenant_required(f):
    """Decorator to ensure tenant context is properly set"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not has_request_context():
            return f(*args, **kwargs)
        
        current_school_id = session.get('school_id')
        user_role = session.get('user_role')
        
        if user_role == 'developer':
            return f(*args, **kwargs)
        
        if not current_school_id:
            from flask import flash, redirect, url_for
            flash('No school access configured. Please contact administrator.', 'error')
            return redirect(url_for('login'))
        
        g.current_school_id = current_school_id
        return f(*args, **kwargs)
    
    return decorated_function

def validate_tenant_access(model_instance, action='read'):
    """Validate if current user can access the model instance"""
    if not has_request_context():
        return True
    
    current_school_id = session.get('school_id')
    user_role = session.get('user_role')
    
    if user_role == 'developer':
        return True
    
    if hasattr(model_instance, 'school_id'):
        if model_instance.school_id != current_school_id:
            return False
    
    return True

class TenantManager:
    """Central manager for tenant operations"""
    
    def __init__(self, app=None, db=None):
        self.app = app
        self.db = db
        if app and db:
            self.init_app(app, db)
    
    def init_app(self, app, db):
        """Initialize tenant enforcement"""
        self.app = app
        self.db = db
        
        @app.before_request
        def set_tenant_context():
            if has_request_context():
                g.current_school_id = session.get('school_id')
                g.user_role = session.get('user_role')
    
    def get_current_tenant(self):
        """Get current tenant ID"""
        if has_request_context():
            return session.get('school_id')
        return None

# Global tenant manager instance
tenant_manager = TenantManager()