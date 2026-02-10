"""
Custom decorators for route protection.
"""
from functools import wraps
from flask import session, redirect, url_for, flash


def login_required(f):
    """Decorator to require user login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def recruiter_required(f):
    """Decorator to require recruiter login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('recruiter_id'):
            flash('Please log in as a recruiter to access this page.', 'warning')
            return redirect(url_for('auth_recruiter.login'))
        if session.get('user_type') != 'recruiter':
            flash('Access denied. Recruiter account required.', 'danger')
            return redirect(url_for('auth_recruiter.login'))
        return f(*args, **kwargs)
    return decorated_function


def api_login_required(f):
    """Decorator for API endpoints requiring user login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            from flask import jsonify
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function


def api_recruiter_required(f):
    """Decorator for API endpoints requiring recruiter login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('recruiter_id') or session.get('user_type') != 'recruiter':
            from flask import jsonify
            return jsonify({'error': 'Unauthorized - Recruiter access required'}), 401
        return f(*args, **kwargs)
    return decorated_function
