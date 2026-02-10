from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models.recruiter_profile import RecruiterProfile
from app.utils.decorators import recruiter_login_required
from app.services.file_service import save_profile_picture

recruiter_profile_bp = Blueprint('recruiter_profile', __name__)

@recruiter_profile_bp.route('/own')
@recruiter_login_required
def own_profile():
    recruiter_id = session['recruiter_id']
    profile = RecruiterProfile.get_by_recruiter_id(recruiter_id)
    return render_template('recruiter/profile/view.html', profile=profile, is_own=True)

@recruiter_profile_bp.route('/edit', methods=['GET', 'POST'])
@recruiter_login_required
def edit():
    recruiter_id = session['recruiter_id']
    if request.method == 'POST':
        data = {
            'headline': request.form.get('headline'),
            'bio': request.form.get('bio'),
            'location': request.form.get('location'),
            'phone': request.form.get('phone')
        }
        
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename != '':
                filename = save_profile_picture(file, recruiter_id) # Reuse user file func, maybe collisions? ID is int.
                # User ID and Recruiter ID are auto-increment integers.
                # Collision possible if Recruiter ID 1 and User ID 1 both upload.
                # save_profile_picture uses {user_id}_{hex}.
                # To avoid collision, let's prefix or rely on hex.
                # But to be safe, I should update save_profile_picture or use a different folder?
                # The function uses `secrets.token_hex(8)` so collision is extremely unlikely.
                data['profile_picture'] = filename
        
        RecruiterProfile.update(recruiter_id, data)
        flash('Profile updated', 'success')
        return redirect(url_for('recruiter_profile.own_profile'))
        
    profile = RecruiterProfile.get_by_recruiter_id(recruiter_id)
    return render_template('recruiter/profile/edit.html', profile=profile)
