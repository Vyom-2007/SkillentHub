"""
Authentication routes blueprint.
Handles user registration, login, logout, and password reset flows.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import timedelta
from app.services import auth_service, otp_service, email_service
from app.utils.decorators import candidate_required, api_candidate_required

auth_bp = Blueprint('auth', __name__, url_prefix='')


@auth_bp.route('/')
def landing():
    """Landing page - redirect to dashboard if logged in, otherwise show landing."""
    if session.get('user_id'):
        return redirect(url_for('auth.dashboard'))
    if session.get('recruiter_id'):
        return redirect(url_for('recruiter.dashboard'))
    return render_template('auth/landing.html')


@auth_bp.route('/dashboard')
def dashboard():
    """Dashboard for logged-in users."""
    if not session.get('user_id'):
        return redirect(url_for('auth.login'))
        
    user_id = session['user_id']
    from app.services import application_service, profile_service, interview_service, notification_service
    
    # Get stats
    stats = application_service.get_application_counts(user_id)
    
    # Get recent applications (limit 5)
    recent_apps = application_service.get_user_applications(user_id, per_page=5)

    # Get profile details (completion, resume status)
    profile = profile_service.get_profile_with_details(user_id)
    if not profile:
        profile = {
            'full_name': session.get('full_name', 'User'),
            'completion': 0,
            'resume_url': None,
            'skills': [],
            'education': [],
            'experience': []
        }

    # Get upcoming interview
    next_interview = interview_service.get_next_upcoming_interview(user_id)

    # Get recent notifications
    notifications = notification_service.get_recent_notifications(user_id, limit=3)

    # Time ago helper
    from datetime import datetime
    def time_ago(dt):
        if not dt: return ''
        now = datetime.now()
        diff = now - dt
        seconds = diff.total_seconds()
        if seconds < 60: return 'Just now'
        elif seconds < 3600: return f'{int(seconds/60)} min ago'
        elif seconds < 86400: return f'{int(seconds/3600)} hr ago'
        elif seconds < 604800: return f'{int(seconds/86400)} days ago'
        else: return dt.strftime('%b %d')
    
    return render_template('auth/dashboard.html', 
                           stats=stats, 
                           recent_apps=recent_apps,
                           profile=profile,
                           next_interview=next_interview,
                           notifications=notifications,
                           time_ago=time_ago)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page."""
    # Redirect if already logged in
    if session.get('user_id'):
        return redirect(url_for('auth.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        full_name = request.form.get('full_name', '').strip()
        
        # Validation
        errors = []
        
        if not email:
            errors.append("Email is required")
        elif not _is_valid_email(email):
            errors.append("Please enter a valid email address")
            
        if not full_name:
            errors.append("Full name is required")
            
        if not password:
            errors.append("Password is required")
        elif len(password) < 8:
            errors.append("Password must be at least 8 characters")
        elif not _is_valid_password(password):
            errors.append("Password must contain at least one uppercase letter and one number")
            
        if password != confirm_password:
            errors.append("Passwords do not match")
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html', 
                                   email=email, 
                                   full_name=full_name)
        
        # Register user
        success, result = auth_service.register_user(email, password, full_name)
        
        if success:
            # Send welcome email (non-blocking)
            email_service.send_welcome_email(email, full_name)
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(result, 'error')
            return render_template('auth/register.html', 
                                   email=email, 
                                   full_name=full_name)
    
    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login page."""
    # Redirect if already logged in
    if session.get('user_id'):
        return redirect(url_for('auth.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Please enter both email and password', 'error')
            return render_template('auth/login.html', email=email)
        
        # Verify credentials
        success, result = auth_service.verify_user(email, password)
        
        if success:
            # Create session
            session.clear()
            session['user_id'] = result['user_id']
            session['email'] = result['email']
            session['full_name'] = result.get('full_name')
            session['profile_picture'] = result.get('profile_picture')
            session.permanent = False  # 30-minute session as per config
            
            flash(f'Welcome back, {result.get("full_name", "User")}!', 'success')
            return redirect(url_for('auth.dashboard'))
        else:
            flash(result, 'error')
            return render_template('auth/login.html', email=email)
    
    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    """Log out the current user."""
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password - request OTP."""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Please enter your email address', 'error')
            return render_template('auth/forgot_password.html')
        
        # Check if user exists
        user = auth_service.get_user_by_email(email)
        
        if not user:
            # Don't reveal if email exists - security best practice
            flash('If an account exists with this email, you will receive an OTP shortly.', 'info')
            return redirect(url_for('auth.forgot_password'))
        
        # Check resend cooldown
        can_resend, seconds_remaining = otp_service.can_resend_otp(email)
        if not can_resend:
            flash(f'Please wait {seconds_remaining} seconds before requesting a new OTP.', 'warning')
            return render_template('auth/forgot_password.html', email=email)
        
        # Get user profile for name
        profile = auth_service.get_user_profile(user['user_id'])
        user_name = profile['full_name'] if profile else "User"
        
        # Generate and send OTP
        # Pass user_id explicitly
        otp, expires_at = otp_service.create_otp(
            user_id=user['user_id'], 
            email=email
        )
        email_service.send_otp_email(email, user_name, otp)
        
        # Store email in session for OTP verification
        session['reset_email'] = email
        
        flash('OTP has been sent to your email address.', 'success')
        return redirect(url_for('auth.verify_otp'))
    
    return render_template('auth/forgot_password.html')


@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    """Verify OTP for password reset."""
    email = session.get('reset_email')
    
    if not email:
        flash('Please request a password reset first.', 'warning')
        return redirect(url_for('auth.forgot_password'))
    
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
            flash('Please enter a valid 6-digit OTP', 'error')
            return render_template('auth/verify_otp.html', 
                                   email=email, 
                                   expiry_seconds=expiry_seconds)
        
        # Verify OTP
        success, message, otp_record = otp_service.verify_otp(email, otp_input)
        
        if success:
            session['otp_verified'] = True
            session['otp_id'] = otp_record['otp_id']
            flash('OTP verified successfully. Please set your new password.', 'success')
            return redirect(url_for('auth.reset_password'))
        else:
            flash(message, 'error')
            # Refresh expiry time
            expiry_seconds = otp_service.get_otp_expiry_seconds(email)
            return render_template('auth/verify_otp.html', 
                                   email=email, 
                                   expiry_seconds=expiry_seconds)
    
    return render_template('auth/verify_otp.html', 
                           email=email, 
                           expiry_seconds=expiry_seconds)


@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    """Resend OTP for password reset."""
    email = session.get('reset_email')
    
    if not email:
        flash('Please request a password reset first.', 'warning')
        return redirect(url_for('auth.forgot_password'))
    
    # Check resend cooldown
    can_resend, seconds_remaining = otp_service.can_resend_otp(email)
    if not can_resend:
        flash(f'Please wait {seconds_remaining} seconds before requesting a new OTP.', 'warning')
        return redirect(url_for('auth.verify_otp'))
    
    # Get user
    user = auth_service.get_user_by_email(email)
    if not user:
        flash('An error occurred. Please try again.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    # Generate and send new OTP
    otp, expires_at = otp_service.create_otp(user['user_id'], email)
    email_service.send_otp_email(email, otp)
    
    flash('A new OTP has been sent to your email.', 'success')
    return redirect(url_for('auth.verify_otp'))


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Reset password after OTP verification."""
    email = session.get('reset_email')
    otp_verified = session.get('otp_verified')
    
    if not email or not otp_verified:
        flash('Please verify your OTP first.', 'warning')
        return redirect(url_for('auth.forgot_password'))
    
    # Verify OTP is still valid
    otp_record = otp_service.get_verified_otp(email)
    if not otp_record:
        session.pop('reset_email', None)
        session.pop('otp_verified', None)
        flash('OTP has expired. Please request a new one.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        errors = []
        
        if not password:
            errors.append("Password is required")
        elif len(password) < 8:
            errors.append("Password must be at least 8 characters")
        elif not _is_valid_password(password):
            errors.append("Password must contain at least one uppercase letter and one number")
            
        if password != confirm_password:
            errors.append("Passwords do not match")
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/reset_password.html')
        
        # Update password
        success = auth_service.update_password(otp_record['user_id'], password)
        
        if success:
            # Mark OTP as used
            otp_service.mark_otp_used(otp_record['otp_id'])
            
            # Clear reset session data
            session.pop('reset_email', None)
            session.pop('otp_verified', None)
            session.pop('otp_id', None)
            
            flash('Password reset successful! Please log in with your new password.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('An error occurred. Please try again.', 'error')
            return render_template('auth/reset_password.html')
    
    return render_template('auth/reset_password.html')


@auth_bp.route('/my-applications')
@candidate_required
def my_applications():
    """View user's applications and registrations."""
    if not session.get('user_id'):
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    from app.services import application_service, event_service
    
    # Fetch applications (Jobs & Internships)
    # Get all without pagination for now, or implement simple pagination
    # For MVP, let's fetch a reasonable limit or all
    applications = application_service.get_user_applications(user_id, per_page=100)
    
    # Fetch registrations (Competitions & Hackathons)
    registrations = event_service.get_user_registrations(user_id)
    
    return render_template('auth/my_applications.html', 
                           applications=applications, 
                           registrations=registrations)


# Helper functions
def _is_valid_email(email):
    """Basic email validation."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def _is_valid_password(password):
    """Validate password has at least one uppercase and one number."""
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    return has_upper and has_digit
    return has_upper and has_digit


@auth_bp.route('/api/applications/<int:application_id>/withdraw', methods=['POST'])
@api_candidate_required
def withdraw_application(application_id):
    """Withdraw an application."""
    if not session.get('user_id'):
        return jsonify({'error': 'Unauthorized'}), 401
        
    user_id = session['user_id']
    from flask import jsonify
    from app.services import application_service
    
    success, result = application_service.withdraw_application(user_id, application_id)
    
    if success:
        return jsonify({'success': True, 'message': result})
    if success:
        return jsonify({'success': True, 'message': result})
    return jsonify({'error': result}), 400


@auth_bp.route('/api/events/cancel', methods=['POST'])
@api_candidate_required
def cancel_event_registration():
    """Cancel event registration."""
    if not session.get('user_id'):
        return jsonify({'error': 'Unauthorized'}), 401
        
    user_id = session['user_id']
    data = request.get_json() or {}
    event_type = data.get('event_type')
    event_id = data.get('event_id')
    
    if not event_type or not event_id:
        return jsonify({'error': 'Missing event details'}), 400
        
    from app.services import event_service
    success, result = event_service.unregister_from_event(user_id, event_type, event_id)
    
    if success:
        return jsonify({'success': True, 'message': result})
    return jsonify({'error': result}), 400


@auth_bp.route('/api/activity-feed')
def get_activity_feed():
    """Get paginated activity feed."""
    # Allow both users and recruiters
    if not session.get('user_id') and not session.get('recruiter_id'):
        return jsonify({'error': 'Unauthorized'}), 401
        
    page = request.args.get('page', 1, type=int)
    filter_type = request.args.get('filter', None)
    
    from app.services import activity_service
    activities = activity_service.get_activity_feed(page=page, filter_type=filter_type)
    
    # Format for JSON response
    feed_data = []
    
    # Helper for time ago
    from datetime import datetime
    def get_time_ago(dt):
        if not dt: return 'Unknown'
        now = datetime.now()
        if isinstance(dt, str): dt = datetime.fromisoformat(dt)
        diff = now - dt
        seconds = diff.total_seconds()
        if seconds < 60: return 'Just now'
        elif seconds < 3600: return f'{int(seconds/60)} min ago'
        elif seconds < 86400: return f'{int(seconds/3600)} hr ago'
        elif seconds < 604800: return f'{int(seconds/86400)} days ago'
        else: return f'{int(seconds/604800)} wks ago'

    try:
        for item in activities:
            try:
                feed_data.append({
                    'id': item['activity_id'],
                    'actor_name': item['actor_name'] or 'Unknown',
                    'actor_picture': item.get('actor_picture'), 
                    'actor_type': item.get('actor_type', 'user'),
                    'action_type': item['action_type'],
                    'item_type': item['item_type'],
                    'item_id': item['item_id'],
                    'details': item['details'], 
                    'created_at': item['created_at'].isoformat() if item.get('created_at') else None,
                    'time_ago': get_time_ago(item.get('created_at'))
                })
            except Exception as e:
                print(f"Error filtering activity item: {e}")
                continue
    except Exception as e:
        print(f"Error processing activity feed: {e}")
        return jsonify({'error': 'Failed to process feed'}), 500
        
    return jsonify({
        'activities': feed_data,
        'has_more': len(feed_data) >= 20 
    })
