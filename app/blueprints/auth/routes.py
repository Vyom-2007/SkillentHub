from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.services.auth_service import AuthService
from app.utils.validators import validate_registration, validate_login

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        
        # Helper validation
        errors = validate_registration(email, password, full_name)
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('auth/register.html', email=email, full_name=full_name)
            
        result = AuthService.register_user(email, password, full_name)
        if 'error' in result:
            flash(result['error'], 'danger')
            return render_template('auth/register.html', email=email, full_name=full_name)
            
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        errors = validate_login(email, password)
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('auth/login.html', email=email)
            
        result = AuthService.login_user(email, password)
        if 'error' in result:
            flash(result['error'], 'danger')
            return render_template('auth/login.html', email=email)
            
        return redirect(url_for('pages.feed')) # Redirect to feed after login
        
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    AuthService.logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

# API Endpoints
@auth_bp.route('/api/auth/register', methods=['POST'])
def api_register():
    data = request.get_json()
    result = AuthService.register_user(data.get('email'), data.get('password'), data.get('full_name'))
    return jsonify(result)

@auth_bp.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json()
    result = AuthService.login_user(data.get('email'), data.get('password'))
    return jsonify(result)

@auth_bp.route('/api/auth/logout', methods=['POST'])
def api_logout():
    result = AuthService.logout_user()
    return jsonify(result)
