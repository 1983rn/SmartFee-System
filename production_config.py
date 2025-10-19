"""
Production configuration for SmartFee Revenue Collection System
"""
import os

class ProductionConfig:
    # Flask
    DEBUG = False
    TESTING = False
    PREFERRED_URL_SCHEME = 'https'
    
    # Security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    
    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_timeout': 30,
        'pool_recycle': 1800,  # Recycle connections after 30 minutes
        'max_overflow': 2
    }
    
    # Gunicorn
    WORKERS = 2
    TIMEOUT = 120
    KEEP_ALIVE = 5
    MAX_REQUESTS = 1000
    MAX_REQUESTS_JITTER = 50
    
    @staticmethod
    def init_app(app):
        # Get database URL from environment
        database_url = os.environ.get('DATABASE_URL')
        if database_url and database_url.startswith("postgres://"):
            app.config['SQLALCHEMY_DATABASE_URI'] = database_url.replace("postgres://", "postgresql://", 1)
        
        # Set secret key
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))
        
        # Enable proxy support for Render
        app.config['PROXY_FIX'] = True
        app.config['PREFERRED_URL_SCHEME'] = 'https'