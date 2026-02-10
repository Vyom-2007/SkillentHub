from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.services.profile_service import ProfileService
from app.services.auth_service import AuthService

profile_bp = Blueprint('profile', __name__, url_prefix='/profile')

@profile_bp.before_request
def login_required():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

@profile_bp.route('/')
def own_profile():
    user = AuthService.get_current_user()
    data = ProfileService.get_full_profile(user['user_id'])
    return render_template('profile/view.html', user=user, **data, is_own=True)

@profile_bp.route('/<int:user_id>')
def view_profile(user_id):
    current_user_id = session.get('user_id')
    if user_id == current_user_id:
        return redirect(url_for('profile.own_profile'))
        
    # TODO: Get other user details (need User model update or service)
    # For now, redirecting to own if not same (mock logic)
    return redirect(url_for('profile.own_profile')) 

@profile_bp.route('/edit', methods=['GET', 'POST'])
def edit_profile():
    user_id = session['user_id']
    user = AuthService.get_current_user()
    
    if request.method == 'POST':
        success = ProfileService.update_profile(user_id, request.form, request.files)
        if success:
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile.own_profile'))
        else:
            flash('Error updating profile.', 'danger')
            
    data = ProfileService.get_full_profile(user_id)
    all_skills = ProfileService.get_all_available_skills()
    return render_template('profile/edit.html', user=user, **data, all_skills=all_skills)

@profile_bp.route('/education/add', methods=['POST'])
def add_education():
    success = ProfileService.add_education(session['user_id'], request.form)
    if success:
        flash('Education added.', 'success')
    else:
        flash('Failed to add education.', 'danger')
    return redirect(url_for('profile.edit_profile'))

@profile_bp.route('/education/<int:edu_id>/delete', methods=['POST'])
def delete_education(edu_id):
    success = ProfileService.delete_education(session['user_id'], edu_id)
    if success:
        flash('Education removed.', 'success')
    else:
        flash('Failed to remove education.', 'danger')
    return redirect(url_for('profile.edit_profile'))

@profile_bp.route('/skills/add', methods=['POST'])
def add_skill():
    skill_id = request.form.get('skill_id')
    proficiency = request.form.get('proficiency')
    success = ProfileService.add_skill(session['user_id'], skill_id, proficiency)
    if success:
        flash('Skill added.', 'success')
    else:
        flash('Failed to add skill.', 'danger')
    return redirect(url_for('profile.edit_profile'))

@profile_bp.route('/skills/<int:skill_id>/delete', methods=['POST'])
def remove_skill(skill_id):
    success = ProfileService.remove_skill(session['user_id'], skill_id)
    if success:
        flash('Skill removed.', 'success')
    else:
        flash('Failed to remove skill.', 'danger')
    return redirect(url_for('profile.edit_profile'))
