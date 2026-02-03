"""
Authentication routes blueprint for user signup, login, logout, and password reset.
"""

from datetime import datetime, timedelta

from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from werkzeug.security import generate_password_hash, check_password_hash

from database.db import execute_query
from auth.forms import SignupForm, LoginForm, ForgotPasswordForm, ResetPasswordForm
from auth.otp import generate_otp, send_otp_email


# Create the authentication blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    Handle user registration.
    - GET: Display the signup form.
    - POST: Validate form, check if email exists, hash password, insert user.
    """
    form = SignupForm()
    
    if form.validate_on_submit():
        full_name = form.full_name.data.strip()
        email = form.email.data.strip().lower()
        password = form.password.data
        
        # Check if email already exists
        existing_user = execute_query(
            "SELECT id FROM users WHERE email = %s",
            (email,),
            fetch_one=True
        )
        
        if existing_user:
            flash('Email already registered. Please use a different email or login.', 'danger')
            return render_template('auth/signup.html', form=form)
        
        # Hash the password
        password_hash = generate_password_hash(password)
        
        # Insert new user with default role 'user'
        result = execute_query(
            "INSERT INTO users (full_name, email, password_hash, role) VALUES (%s, %s, %s, %s)",
            (full_name, email, password_hash, 'user'),
            commit=True
        )
        
        if result:
            flash('Account created successfully! Please login.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('An error occurred during registration. Please try again.', 'danger')
    
    return render_template('auth/signup.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login.
    - GET: Display the login form.
    - POST: Validate credentials and create session.
    """
    # Redirect if already logged in
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        password = form.password.data
        
        # Fetch user by email
        user = execute_query(
            "SELECT id, full_name, email, password_hash, role FROM users WHERE email = %s",
            (email,),
            fetch_one=True
        )
        
        if user and check_password_hash(user['password_hash'], password):
            # Store user info in session
            session['user_id'] = user['id']
            session['user_name'] = user['full_name']
            session['user_email'] = user['email']
            session['role'] = user['role']
            
            flash(f'Welcome back, {user["full_name"]}!', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
    
    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
def logout():
    """
    Handle user logout by clearing the session.
    """
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """
    Handle forgot password request.
    - GET: Display the forgot password form.
    - POST: Validate email, generate OTP, store in DB, send email.
    """
    form = ForgotPasswordForm()
    
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        
        # Check if email exists in users table
        user = execute_query(
            "SELECT id FROM users WHERE email = %s",
            (email,),
            fetch_one=True
        )
        
        if not user:
            flash('No account found with that email address.', 'danger')
            return render_template('auth/forgot_password.html', form=form)
        
        # Generate OTP and calculate expiration time (10 minutes from now)
        otp = generate_otp()
        expires_at = datetime.now() + timedelta(minutes=10)
        
        # Delete any existing OTP for this email
        execute_query(
            "DELETE FROM password_resets WHERE email = %s",
            (email,),
            commit=True
        )
        
        # Insert new OTP record
        result = execute_query(
            "INSERT INTO password_resets (email, otp_code, expires_at) VALUES (%s, %s, %s)",
            (email, otp, expires_at),
            commit=True
        )
        
        if result is not None:
            # Send OTP email (simulated)
            send_otp_email(email, otp)
            
            # Store email in session for the reset page
            session['reset_email'] = email
            
            flash('OTP has been sent to your email. Please check your inbox.', 'success')
            return redirect(url_for('auth.reset_password'))
        else:
            flash('An error occurred. Please try again.', 'danger')
    
    return render_template('auth/forgot_password.html', form=form)


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """
    Handle password reset with OTP verification.
    - GET: Display the reset password form.
    - POST: Validate OTP, update password, delete OTP record.
    """
    # Check if user came from forgot password page
    if 'reset_email' not in session:
        flash('Please request a password reset first.', 'warning')
        return redirect(url_for('auth.forgot_password'))
    
    email = session['reset_email']
    form = ResetPasswordForm()
    
    if form.validate_on_submit():
        otp = form.otp.data.strip()
        new_password = form.new_password.data
        
        # Validate OTP against database
        otp_record = execute_query(
            """
            SELECT email, otp_code, expires_at 
            FROM password_resets 
            WHERE email = %s AND otp_code = %s AND expires_at > NOW()
            """,
            (email, otp),
            fetch_one=True
        )
        
        if not otp_record:
            flash('Invalid or expired OTP. Please request a new one.', 'danger')
            return render_template('auth/reset_password.html', form=form, email=email)
        
        # Hash the new password
        password_hash = generate_password_hash(new_password)
        
        # Update user's password
        update_result = execute_query(
            "UPDATE users SET password_hash = %s WHERE email = %s",
            (password_hash, email),
            commit=True
        )
        
        if update_result is not None:
            # Delete the used OTP record
            execute_query(
                "DELETE FROM password_resets WHERE email = %s",
                (email,),
                commit=True
            )
            
            # Clear the reset email from session
            session.pop('reset_email', None)
            
            flash('Password reset successfully! Please login with your new password.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('An error occurred while resetting your password. Please try again.', 'danger')
    
    return render_template('auth/reset_password.html', form=form, email=email)
