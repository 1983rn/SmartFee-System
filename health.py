from flask import Blueprint, jsonify
from app import create_app

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health_check():
    """Health check endpoint for Render"""
    return jsonify({
        'status': 'ok',
        'message': 'Service is running',
        'version': '1.0.0'
    })
