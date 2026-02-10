from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models.recruiter import Recruiter
from app.models.otp import PasswordResetOTP
from app.services.email_service import send_otp_email
from app.utils.validators import validate_email, validate_password
from app.database.connection import get_db
import bcrypt

recruiter_auth_bp = Blueprint('recruiter_auth', __name__)

@recruiter_auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not full_name or not email or not password:
            flash('All fields are required', 'danger')
            return redirect(url_for('recruiter_auth.register'))
            
        if not validate_email(email):
            flash('Invalid email format', 'danger')
            return redirect(url_for('recruiter_auth.register'))
            
        if not validate_password(password):
            flash('Password must be at least 8 chars, 1 uppercase, 1 number', 'danger')
            return redirect(url_for('recruiter_auth.register'))
            
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('recruiter_auth.register'))
            
        if Recruiter.get_by_email(email):
            flash('Email already registered', 'danger')
            return redirect(url_for('recruiter_auth.register'))
            
        try:
            Recruiter.create(email, password, full_name)
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('recruiter_auth.login'))
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'danger')
            return redirect(url_for('recruiter_auth.register'))
            
    return render_template('recruiter/register.html')

@recruiter_auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        recruiter = Recruiter.get_by_email(email)
        
        if recruiter and Recruiter.verify_password(recruiter['password_hash'], password):
            session['recruiter_id'] = recruiter['recruiter_id']
            session['full_name'] = recruiter['full_name']
            session['role'] = 'recruiter'
            flash('Login successful!', 'success')
            return redirect(url_for('recruiter_dashboard.index'))
        else:
            flash('Invalid email or password', 'danger')
            
    return render_template('recruiter/login.html')

@recruiter_auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index')) # Redirect to main index or recruiter login? Main index is better.

@recruiter_auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        recruiter = Recruiter.get_by_email(email)
        if recruiter:
            # Pass recruiter_id
            otp = PasswordResetOTP.create(email, recruiter_id=recruiter['recruiter_id'])
            if send_otp_email(email, otp):
                session['recruiter_reset_email'] = email
                flash('OTP sent to your email', 'success')
                return redirect(url_for('recruiter_auth.verify_otp'))
            else:
                flash('Failed to send email. Check configuration.', 'danger')
        else:
            flash('If an account exists, an OTP has been sent.', 'info')
            session['recruiter_reset_email'] = email
            return redirect(url_for('recruiter_auth.verify_otp'))
    return render_template('recruiter/forgot_password.html')

@recruiter_auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    email = session.get('recruiter_reset_email')
    if not email:
        return redirect(url_for('recruiter_auth.forgot_password'))
        
    if request.method == 'POST':
        otp = request.form.get('otp')
        valid, record = PasswordResetOTP.verify(email, otp)
        if valid:
            session['recruiter_reset_otp_id'] = record['otp_id']
            PasswordResetOTP.mark_used(record['otp_id'])
            return redirect(url_for('recruiter_auth.reset_password'))
        else:
            flash('Invalid or expired OTP', 'danger')
            
    return render_template('recruiter/verify_otp.html', email=email)

@recruiter_auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if 'recruiter_reset_otp_id' not in session:
        return redirect(url_for('recruiter_auth.forgot_password'))
        
    if request.method == 'POST':
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        
        if password != confirm:
            flash('Passwords do not match', 'danger')
        elif not validate_password(password):
            flash('Password too weak', 'danger')
        else:
            email = session.get('recruiter_reset_email')
            
            db = get_db()
            cursor = db.cursor()
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            # Update recruiters table
            cursor.execute("UPDATE recruiters SET password_hash = %s WHERE email = %s", (hashed, email))
            db.commit()
            cursor.close()
            
            session.pop('recruiter_reset_email', None)
            session.pop('recruiter_reset_otp_id', None)
            flash('Password reset successful. Login now.', 'success')
            return redirect(url_for('recruiter_auth.login'))
            
    return render_template('recruiter/reset_password.html')
