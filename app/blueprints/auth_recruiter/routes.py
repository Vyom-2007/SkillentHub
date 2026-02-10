"""
Recruiter authentication routes.
Handles registration, login, and logout with session isolation.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from functools import wraps
import bcrypt
import logging
from app.models import recruiter as recruiter_model

auth_recruiter_bp = Blueprint('auth_recruiter', __name__, url_prefix='/recruiter')


def clear_user_session():
    """Clear regular user session keys to ensure isolation."""
    keys_to_remove = ['user_id', 'user_email', 'user_name']
    for key in keys_to_remove:
        session.pop(key, None)


def clear_recruiter_session():
    """Clear recruiter session keys."""
    keys_to_remove = ['recruiter_id', 'recruiter_email', 'company_name', 'user_type']
    for key in keys_to_remove:
        session.pop(key, None)


# ========== REGISTRATION ==========

@auth_recruiter_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Recruiter registration page."""
    if session.get('recruiter_id'):
        return redirect(url_for('recruiter.dashboard'))
    
    if request.method == 'POST':
        company_name = request.form.get('company_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        errors = []
        if not company_name or len(company_name) < 2:
            errors.append("Company name must be at least 2 characters")
        if not email or '@' not in email:
            errors.append("Valid email required")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters")
        if password != confirm_password:
            errors.append("Passwords do not match")
        
        # Check email uniqueness
        if recruiter_model.email_exists(email):
            errors.append("Email already registered")
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('recruiter/register.html', 
                                   company_name=company_name, 
                                   email=email)
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create recruiter
        recruiter_id, error = recruiter_model.create(company_name, email, password_hash)
        
        if recruiter_id:
            flash("Registration successful! Please log in.", 'success')
            return redirect(url_for('auth_recruiter.login'))
        else:
            flash(error or "Registration failed", 'danger')
    
    return render_template('recruiter/register.html')


# ========== LOGIN ==========

@auth_recruiter_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Recruiter login page."""
    if session.get('recruiter_id'):
        return redirect(url_for('recruiter.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash("Email and password required", 'danger')
            return render_template('recruiter/login.html', email=email)
        
        # Get recruiter
        recruiter = recruiter_model.get_by_email(email)
        
        if not recruiter:
            flash("Invalid email or password", 'danger')
            return render_template('recruiter/login.html', email=email)
        
        # Check if active
        if not recruiter.get('is_active', True):
            flash("Account is deactivated. Contact support.", 'danger')
            return render_template('recruiter/login.html', email=email)
        
        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), recruiter['password_hash'].encode('utf-8')):
            flash("Invalid email or password", 'danger')
            return render_template('recruiter/login.html', email=email)
        
        # SUCCESS: Clear any user session first (session isolation)
        clear_user_session()
        
        # Set recruiter session
        session['recruiter_id'] = recruiter['recruiter_id']
        session['recruiter_email'] = recruiter['company_email']
        session['company_name'] = recruiter['company_name']
        session['user_type'] = 'recruiter'
        
        flash(f"Welcome, {recruiter['company_name']}!", 'success')
        logging.info(f"DEBUG: Login successful for {email}. Redirecting to {url_for('recruiter.dashboard')}")
        logging.info(f"DEBUG: Session: {session}")
        return redirect(url_for('recruiter.dashboard'))
    
    return render_template('recruiter/login.html')


# ========== LOGOUT ==========

@auth_recruiter_bp.route('/logout')
def logout():
    """Logout recruiter."""
    clear_recruiter_session()
    flash("You have been logged out.", 'info')
    return redirect(url_for('auth_recruiter.login'))
