"""
Custom decorators for route protection.
"""
from functools import wraps
from flask import session, redirect, url_for, flash



from flask import abort

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
        # If logged in as a regular user, forbid access (Strict RBAC)
        if session.get('user_id') and not session.get('recruiter_id'):
             abort(403)
        
        # If not logged in at all, redirect to login
        if not session.get('recruiter_id'):
            flash('Please log in as a recruiter to access this page.', 'warning')
            return redirect(url_for('auth_recruiter.login'))
            
        # Double check user type
        if session.get('user_type') != 'recruiter':
            abort(403)
            
        return f(*args, **kwargs)
    return decorated_function


def candidate_required(f):
    """Decorator to require candidate (regular user) login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # If logged in as a recruiter, forbid access (Strict RBAC)
        if session.get('recruiter_id'):
            abort(403)
            
        if not session.get('user_id'):
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
            
        return f(*args, **kwargs)
    return decorated_function


def api_login_required(f):
    """Decorator for API endpoints requiring user login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id') and not session.get('recruiter_id'):
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
            return jsonify({'error': 'Forbidden - Recruiter access required'}), 403
        return f(*args, **kwargs)
    return decorated_function


def api_candidate_required(f):
    """Decorator for API endpoints requiring candidate login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('recruiter_id'):
            from flask import jsonify
            return jsonify({'error': 'Forbidden - Candidate access required'}), 403
            
        if not session.get('user_id'):
            from flask import jsonify
            return jsonify({'error': 'Unauthorized'}), 401
            
        return f(*args, **kwargs)
    return decorated_function
