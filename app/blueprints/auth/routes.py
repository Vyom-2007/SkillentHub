import re
from flask import render_template, request, redirect, url_for, session, flash, jsonify
from app.blueprints.auth import auth_bp
from app.services.auth_service import (
    find_user_by_email,
    create_user,
    verify_password,
    update_password,
    update_last_login,
)
from app.services.otp_service import generate_otp, verify_otp, is_otp_verified, mark_otp_used
from app.services.email_service import send_otp_email


# ──────────────────────────────────────────────────────────
# Registration
# ──────────────────────────────────────────────────────────

@auth_bp.route('/register', methods=['GET'])
def register_page():
    if 'user_id' in session:
        return redirect(url_for('auth.feed_redirect'))
    return render_template('auth/register.html')


@auth_bp.route('/register', methods=['POST'])
def register():
    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')

    # Server-side validation
    errors = []
    if not full_name:
        errors.append('Full name is required.')
    if not email or not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
        errors.append('A valid email address is required.')
    if len(password) < 8 or not re.search(r'[A-Z]', password) or not re.search(r'[0-9]', password):
        errors.append('Password must be at least 8 characters with 1 uppercase letter and 1 number.')

    if errors:
        for err in errors:
            flash(err, 'danger')
        return redirect(url_for('auth.register_page'))

    # Check uniqueness
    if find_user_by_email(email):
        flash('An account with this email already exists.', 'danger')
        return redirect(url_for('auth.register_page'))

    create_user(full_name, email, password)
    flash('Registration successful! Please log in.', 'success')
    return redirect(url_for('auth.login_page'))


# ──────────────────────────────────────────────────────────
# Login
# ──────────────────────────────────────────────────────────

@auth_bp.route('/login', methods=['GET'])
def login_page():
    if 'user_id' in session:
        return redirect(url_for('auth.feed_redirect'))
    return render_template('auth/login.html')


@auth_bp.route('/login', methods=['POST'])
def login():
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')

    user = find_user_by_email(email)

    if not user or not verify_password(password, user['password_hash']):
        flash('Invalid credentials. Please try again.', 'danger')
        return redirect(url_for('auth.login_page'))

    if not user.get('is_active', True):
        flash('Your account has been deactivated.', 'danger')
        return redirect(url_for('auth.login_page'))

    # Set session
    session.permanent = True
    session['user_id'] = user['user_id']
    session['user_email'] = user['email']
    session['user_name'] = user['full_name']

    update_last_login(user['user_id'])
    return redirect(url_for('auth.feed_redirect'))


@auth_bp.route('/feed')
def feed_redirect():
    """Temporary placeholder until the feed blueprint is built."""
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))
    return f"""
    <html><body style="font-family:Inter,sans-serif;display:flex;align-items:center;
    justify-content:center;height:100vh;background:#f5f5ff;">
    <div style="text-align:center;">
        <h1>Welcome, {session.get('user_name', 'User')}!</h1>
        <p>Feed page coming soon.</p>
        <form action="{url_for('auth.logout')}" method="post">
            <button type="submit" style="padding:10px 28px;background:#4f46e5;color:#fff;
            border:none;border-radius:8px;cursor:pointer;font-size:16px;">Log Out</button>
        </form>
    </div></body></html>
    """


# ──────────────────────────────────────────────────────────
# Logout
# ──────────────────────────────────────────────────────────

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('pages.landing'))


# ──────────────────────────────────────────────────────────
# Forgot Password — Step A: Request OTP
# ──────────────────────────────────────────────────────────

@auth_bp.route('/forgot-password', methods=['GET'])
def forgot_password_page():
    return render_template('auth/forgot_password.html')


@auth_bp.route('/forgot-password/send-otp', methods=['POST'])
def send_otp():
    email = request.form.get('email', '').strip().lower()

    if not email:
        flash('Please enter your email address.', 'danger')
        return redirect(url_for('auth.forgot_password_page'))

    user = find_user_by_email(email)
    if not user:
        # Don't reveal whether the email exists
        flash('If an account with that email exists, an OTP has been sent.', 'info')
        return redirect(url_for('auth.verify_otp_page', email=email))

    otp_code = generate_otp(user['user_id'], email)
    result = send_otp_email(email, otp_code)

    if result is not True:
        # Email sending failed — still let user proceed (OTP is in DB)
        print(f"[EMAIL ERROR] {result}")

    flash('If an account with that email exists, an OTP has been sent.', 'info')
    return redirect(url_for('auth.verify_otp_page', email=email))


# ──────────────────────────────────────────────────────────
# Forgot Password — Step B: Verify OTP
# ──────────────────────────────────────────────────────────

@auth_bp.route('/verify-otp', methods=['GET'])
def verify_otp_page():
    email = request.args.get('email', '')
    return render_template('auth/verify_otp.html', email=email)


@auth_bp.route('/forgot-password/verify-otp', methods=['POST'])
def verify_otp_api():
    data = request.get_json() if request.is_json else request.form
    email = data.get('email', '').strip().lower()
    otp_code = data.get('otp', '').strip()

    if not email or not otp_code:
        return jsonify({'success': False, 'message': 'Email and OTP are required.'}), 400

    result = verify_otp(email, otp_code)
    status_code = 200 if result['success'] else 400
    return jsonify(result), status_code


# ──────────────────────────────────────────────────────────
# Forgot Password — Step C: Reset Password
# ──────────────────────────────────────────────────────────

@auth_bp.route('/reset-password', methods=['GET'])
def reset_password_page():
    email = request.args.get('email', '')
    return render_template('auth/reset_password.html', email=email)


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')

    if not email or not password:
        flash('All fields are required.', 'danger')
        return redirect(url_for('auth.reset_password_page', email=email))

    if password != confirm_password:
        flash('Passwords do not match.', 'danger')
        return redirect(url_for('auth.reset_password_page', email=email))

    if len(password) < 8 or not re.search(r'[A-Z]', password) or not re.search(r'[0-9]', password):
        flash('Password must be at least 8 characters with 1 uppercase letter and 1 number.', 'danger')
        return redirect(url_for('auth.reset_password_page', email=email))

    # Ensure OTP was verified
    otp_record = is_otp_verified(email)
    if not otp_record:
        flash('OTP verification required before resetting password.', 'danger')
        return redirect(url_for('auth.forgot_password_page'))

    user = find_user_by_email(email)
    if not user:
        flash('No account found with that email.', 'danger')
        return redirect(url_for('auth.forgot_password_page'))

    update_password(user['user_id'], password)
    mark_otp_used(otp_record['otp_id'])

    flash('Password reset successful! Please log in with your new password.', 'success')
    return redirect(url_for('auth.login_page'))
