"""
Settings routes.
Handles user account settings including password change and privacy controls.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from functools import wraps
from app.services import user_service

settings_bp = Blueprint('settings', __name__)


def login_required(f):
    """Decorator to require login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@settings_bp.route('/settings')
@login_required
def settings():
    """Display settings page."""
    user_id = session.get('user_id')
    user = user_service.get_user_by_id(user_id)
    privacy = user_service.get_privacy_settings(user_id)
    
    return render_template('settings/settings.html',
                           user=user,
                           privacy=privacy)


@settings_bp.route('/settings/password', methods=['POST'])
@login_required
def change_password():
    """Handle password change."""
    user_id = session.get('user_id')
    
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    # Validate inputs
    if not current_password or not new_password:
        flash('Please fill in all password fields.', 'error')
        return redirect(url_for('settings.settings'))
    
    if new_password != confirm_password:
        flash('New passwords do not match.', 'error')
        return redirect(url_for('settings.settings'))
    
    # Validate password complexity
    valid, error_msg = user_service.validate_password_complexity(new_password)
    if not valid:
        flash(error_msg, 'error')
        return redirect(url_for('settings.settings'))
    
    # Verify current password
    if not user_service.verify_password(user_id, current_password):
        flash('Incorrect current password.', 'error')
        return redirect(url_for('settings.settings'))
    
    # Update password
    user_service.update_password(user_id, new_password)
    flash('Password changed successfully!', 'success')
    
    return redirect(url_for('settings.settings'))


@settings_bp.route('/settings/privacy', methods=['POST'])
@login_required
def update_privacy():
    """Handle privacy settings update."""
    user_id = session.get('user_id')
    
    visibility = request.form.get('visibility', 'public')
    show_email = request.form.get('show_email') == 'on'
    show_phone = request.form.get('show_phone') == 'on'
    
    # Validate visibility
    if visibility not in ['public', 'registered_only', 'private']:
        visibility = 'public'
    
    # Update settings
    user_service.update_privacy_settings(user_id, visibility, show_email, show_phone)
    flash('Privacy settings updated successfully!', 'success')
    
    return redirect(url_for('settings.settings'))


# API Endpoint for AJAX
@settings_bp.route('/api/settings/privacy', methods=['POST'])
def api_update_privacy():
    """API endpoint for privacy settings update."""
    if not session.get('user_id'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session.get('user_id')
    data = request.get_json() or {}
    
    visibility = data.get('visibility', 'public')
    show_email = bool(data.get('show_email', True))
    show_phone = bool(data.get('show_phone', False))
    
    if visibility not in ['public', 'registered_only', 'private']:
        visibility = 'public'
    
    user_service.update_privacy_settings(user_id, visibility, show_email, show_phone)
    
    return jsonify({'success': True})
