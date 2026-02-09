"""
Recruiter Settings Routes.
View and update profile, change password.
"""
from flask import render_template, request, redirect, url_for, flash, session
from app.blueprints.recruiter.routes import recruiter_bp
from app.utils.decorators import recruiter_required
from app.services import recruiter_settings_service

@recruiter_bp.route('/settings')
@recruiter_required
def settings():
    recruiter_id = session.get('recruiter_id')
    profile = recruiter_settings_service.get_profile(recruiter_id)
    
    return render_template('recruiter/settings.html', profile=profile)

@recruiter_bp.route('/settings/profile', methods=['POST'])
@recruiter_required
def update_profile():
    recruiter_id = session.get('recruiter_id')
    company_name = request.form.get('company_name')
    
    if company_name:
        recruiter_settings_service.update_profile(recruiter_id, company_name)
        flash('Profile updated successfully!', 'success')
        
    return redirect(url_for('recruiter.settings'))

@recruiter_bp.route('/settings/password', methods=['POST'])
@recruiter_required
def change_password():
    recruiter_id = session.get('recruiter_id')
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if new_password != confirm_password:
        flash('New passwords do not match.', 'danger')
        return redirect(url_for('recruiter.settings'))
        
    success, message = recruiter_settings_service.change_password(recruiter_id, current_password, new_password)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
        
    return redirect(url_for('recruiter.settings'))
