from functools import wraps
from flask import make_response

def add_security_headers(response):
    """Add security headers to response"""
    # Content Security Policy
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com; "
        "font-src 'self' cdnjs.cloudflare.com; "
        "img-src 'self' data:; "
        "form-action 'self'"
    )
    
    # Other security headers
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'same-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    
    # Add caching headers for static files
    if any(response.mimetype.startswith(t) for t in ['text/css', 'application/javascript', 'image/']):
        response.headers['Cache-Control'] = 'public, max-age=31536000'
    else:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    
    return response

def init_security(app):
    """Initialize security features for the Flask app"""
    # Enable HSTS
    if app.config.get('PREFERRED_URL_SCHEME') == 'https':
        app.config['SSLIFY_PERMANENT'] = True
        
    # Add security headers to all responses
    app.after_request(add_security_headers)