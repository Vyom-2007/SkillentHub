
"""
Recruiter authentication routes.
Handles registration, login, and logout with session isolation.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from functools import wraps
import logging
from app.services import recruiter_auth_service

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
        if recruiter_auth_service.email_exists(email):
            errors.append("Email already registered")
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('recruiter/register.html', 
                                   company_name=company_name, 
                                   email=email)
        
        # Create recruiter via service
        success, result = recruiter_auth_service.register_recruiter(company_name, email, password)
        
        if success:
            flash("Registration successful! Please log in.", 'success')
            return redirect(url_for('auth_recruiter.login'))
        else:
            flash(result or "Registration failed", 'danger')
    
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
        
        # Verify credentials via service
        success, result = recruiter_auth_service.verify_recruiter(email, password)
        
        if not success:
            flash(result, 'danger')
            return render_template('recruiter/login.html', email=email)
        
        recruiter = result
        
        # SUCCESS: Clear any user session first (session isolation)
        clear_user_session()
        
        # Set recruiter session
        session['recruiter_id'] = recruiter['recruiter_id']
        session['recruiter_email'] = recruiter['company_email']
        session['company_name'] = recruiter['company_name']
        session['user_type'] = 'recruiter'
        
        flash(f"Welcome, {recruiter['company_name']}!", 'success')
        logging.info(f"DEBUG: Login successful for {email}. Redirecting to {url_for('recruiter.dashboard')}")
        return redirect(url_for('recruiter.dashboard'))
    
    return render_template('recruiter/login.html')


# ========== LOGOUT ==========

@auth_recruiter_bp.route('/logout')
def logout():
    """Logout recruiter."""
    clear_recruiter_session()
    flash("You have been logged out.", 'info')
    return redirect(url_for('auth_recruiter.login'))


# ========== FORGOT PASSWORD ==========

@auth_recruiter_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password - request OTP."""
    from app.services import otp_service, email_service
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Please enter your company email address', 'danger')
            return render_template('recruiter/forgot_password.html')
        
        # Initiate password reset via service
        success, result = recruiter_auth_service.initiate_password_reset(email)
        
        if success:
             # Store email in session for OTP verification
            session['recruiter_reset_email'] = email
            flash(result, 'success')
            return redirect(url_for('auth_recruiter.verify_otp'))
        else:
            # If email not found, don't reveal it (security), unless it's a validation error
            if result == "Email not found.":
                 flash('If an account exists with this email, you will receive an OTP shortly.', 'info')
            else:
                 flash(result, 'warning')
            return render_template('recruiter/forgot_password.html', email=email)
    
    return render_template('recruiter/forgot_password.html')


@auth_recruiter_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    """Verify OTP for password reset."""
    from app.services import otp_service
    
    email = session.get('recruiter_reset_email')
    
    if not email:
        flash('Please request a password reset first.', 'warning')
        return redirect(url_for('auth_recruiter.forgot_password'))
    
    # Get expiry time for countdown
    expiry_seconds = otp_service.get_otp_expiry_seconds(email)
    
    if request.method == 'POST':
        # Collect OTP from 6 separate inputs
        otp_digits = []
        for i in range(1, 7):
            digit = request.form.get(f'otp{i}', '')
            otp_digits.append(digit)
        
        otp_input = ''.join(otp_digits)
        
        if len(otp_input) != 6 or not otp_input.isdigit():
            flash('Please enter a valid 6-digit OTP', 'danger')
            return render_template('recruiter/verify_otp.html', 
                                   email=email, 
                                   expiry_seconds=expiry_seconds)
        
        # Verify OTP
        success, message, otp_record = otp_service.verify_otp(email, otp_input)
        
        if success:
            session['recruiter_otp_verified'] = True
            session['recruiter_otp_id'] = otp_record['otp_id']
            flash('OTP verified successfully. Please set your new password.', 'success')
            return redirect(url_for('auth_recruiter.reset_password'))
        else:
            flash(message, 'danger')
            # Refresh expiry time
            expiry_seconds = otp_service.get_otp_expiry_seconds(email)
            return render_template('recruiter/verify_otp.html', 
                                   email=email, 
                                   expiry_seconds=expiry_seconds)
    
    return render_template('recruiter/verify_otp.html', 
                           email=email, 
                           expiry_seconds=expiry_seconds)


@auth_recruiter_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    """Resend OTP for password reset."""
    from app.services import otp_service, email_service
    
    email = session.get('recruiter_reset_email')
    
    if not email:
        flash('Please request a password reset first.', 'warning')
        return redirect(url_for('auth_recruiter.forgot_password'))
    
    # Initiate password reset via service (handles resend logic)
    success, result = recruiter_auth_service.initiate_password_reset(email)
    
    if success:
        flash(result, 'success')
        return redirect(url_for('auth_recruiter.verify_otp'))
    else:
        flash(result, 'danger')
        return redirect(url_for('auth_recruiter.forgot_password'))


@auth_recruiter_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Reset password after OTP verification."""
    from app.services import otp_service
    
    email = session.get('recruiter_reset_email')
    otp_verified = session.get('recruiter_otp_verified')
    
    if not email or not otp_verified:
        flash('Please verify your OTP first.', 'warning')
        return redirect(url_for('auth_recruiter.forgot_password'))
    
    # Verify OTP is still valid
    otp_record = otp_service.get_verified_otp(email)
    if not otp_record:
        session.pop('recruiter_reset_email', None)
        session.pop('recruiter_otp_verified', None)
        flash('OTP has expired. Please request a new one.', 'danger')
        return redirect(url_for('auth_recruiter.forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        errors = []
        
        if not password:
            errors.append("Password is required")
        elif len(password) < 8:
            errors.append("Password must be at least 8 characters")
            
        if password != confirm_password:
            errors.append("Passwords do not match")
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('recruiter/reset_password.html')
        
        # Use recruiter_id from OTP record if available, or fetch by email
        recruiter_id = otp_record.get('recruiter_id')
        if not recruiter_id:
             # Fallback if recruiter_id wasn't in OTP (legacy?)
             recruiter = recruiter_auth_service.get_recruiter_by_email(email)
             if recruiter:
                 recruiter_id = recruiter['recruiter_id']
        
        if recruiter_id:
            try:
                # Update password via service
                recruiter_auth_service.update_password(recruiter_id, password)
                success = True
            except Exception as e:
                current_app.logger.error(f"Failed to update password: {e}")
                success = False
        else:
            success = False
        
        if success:
            # Mark OTP as used
            otp_service.mark_otp_used(otp_record['otp_id'])
            
            # Clear reset session data
            session.pop('recruiter_reset_email', None)
            session.pop('recruiter_otp_verified', None)
            session.pop('recruiter_otp_id', None)
            
            flash('Password reset successful! Please log in with your new password.', 'success')
            return redirect(url_for('auth_recruiter.login'))
        else:
            flash('An error occurred. Please try again.', 'danger')
            return render_template('recruiter/reset_password.html')
    
    return render_template('recruiter/reset_password.html')
