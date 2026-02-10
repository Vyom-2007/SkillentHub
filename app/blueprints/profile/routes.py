import json
from flask import (
    render_template, request, redirect, url_for,
    session, flash,
)
from app.blueprints.profile import profile_bp
from app.utils.decorators import login_required
from app.services.profile_service import (
    get_full_profile,
    upsert_profile,
    save_skills,
    save_education,
    update_profile_completion,
    increment_visit,
)
from app.services.file_service import save_profile_picture, save_document
from app.services.connection_service import get_connection_status


# ──────────────────────────────────────────────────────────
# Profile Setup
# ──────────────────────────────────────────────────────────

@profile_bp.route('/setup', methods=['GET'])
@login_required
def setup_page():
    return render_template('profile/setup.html')


@profile_bp.route('/setup', methods=['POST'])
@login_required
def setup():
    user_id = session['user_id']

    # Collect profile fields
    profile_data = {
        'headline': request.form.get('headline', '').strip(),
        'bio': request.form.get('bio', '').strip(),
        'location': request.form.get('location', '').strip(),
        'phone': request.form.get('phone', '').strip(),
    }

    # Handle file uploads
    try:
        pic = request.files.get('profile_picture')
        if pic and pic.filename:
            profile_data['profile_picture'] = save_profile_picture(pic, user_id)

        resume = request.files.get('resume')
        if resume and resume.filename:
            profile_data['resume_path'] = save_document(resume, user_id, 'resume')

        cover_letter = request.files.get('cover_letter')
        if cover_letter and cover_letter.filename:
            profile_data['cover_letter_path'] = save_document(cover_letter, user_id, 'cover_letter')
    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('profile.setup_page'))

    # Save profile
    upsert_profile(user_id, profile_data)

    # Save skills (JSON from hidden input)
    skills_json = request.form.get('skills_json', '[]')
    try:
        skills_list = json.loads(skills_json)
        if skills_list:
            save_skills(user_id, skills_list)
    except (json.JSONDecodeError, TypeError):
        pass

    # Save education (dynamic rows)
    institutions = request.form.getlist('institution[]')
    degrees = request.form.getlist('degree[]')
    fields = request.form.getlist('field_of_study[]')
    start_dates = request.form.getlist('start_date[]')
    end_dates = request.form.getlist('end_date[]')
    descriptions = request.form.getlist('edu_description[]')

    edu_list = []
    for i in range(len(institutions)):
        if institutions[i].strip():
            edu_list.append({
                'institution': institutions[i],
                'degree': degrees[i] if i < len(degrees) else '',
                'field_of_study': fields[i] if i < len(fields) else '',
                'start_date': start_dates[i] if i < len(start_dates) else None,
                'end_date': end_dates[i] if i < len(end_dates) else None,
                'description': descriptions[i] if i < len(descriptions) else '',
            })

    if edu_list:
        save_education(user_id, edu_list)

    # Update completion
    update_profile_completion(user_id)

    flash('Profile setup complete!', 'success')
    return redirect(url_for('profile.own_profile'))


# ──────────────────────────────────────────────────────────
# Profile Edit
# ──────────────────────────────────────────────────────────

@profile_bp.route('/edit', methods=['GET'])
@login_required
def edit_page():
    user_id = session['user_id']
    data = get_full_profile(user_id)
    return render_template('profile/edit.html', data=data)


@profile_bp.route('/edit', methods=['POST'])
@login_required
def edit():
    user_id = session['user_id']

    profile_data = {
        'headline': request.form.get('headline', '').strip(),
        'bio': request.form.get('bio', '').strip(),
        'location': request.form.get('location', '').strip(),
        'phone': request.form.get('phone', '').strip(),
    }

    # Handle file uploads
    try:
        pic = request.files.get('profile_picture')
        if pic and pic.filename:
            profile_data['profile_picture'] = save_profile_picture(pic, user_id)

        resume = request.files.get('resume')
        if resume and resume.filename:
            profile_data['resume_path'] = save_document(resume, user_id, 'resume')

        cover_letter = request.files.get('cover_letter')
        if cover_letter and cover_letter.filename:
            profile_data['cover_letter_path'] = save_document(cover_letter, user_id, 'cover_letter')
    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('profile.edit_page'))

    upsert_profile(user_id, profile_data)

    # Skills
    skills_json = request.form.get('skills_json', '[]')
    try:
        skills_list = json.loads(skills_json)
        save_skills(user_id, skills_list)
    except (json.JSONDecodeError, TypeError):
        pass

    # Education
    institutions = request.form.getlist('institution[]')
    degrees = request.form.getlist('degree[]')
    fields = request.form.getlist('field_of_study[]')
    start_dates = request.form.getlist('start_date[]')
    end_dates = request.form.getlist('end_date[]')
    descriptions = request.form.getlist('edu_description[]')

    edu_list = []
    for i in range(len(institutions)):
        if institutions[i].strip():
            edu_list.append({
                'institution': institutions[i],
                'degree': degrees[i] if i < len(degrees) else '',
                'field_of_study': fields[i] if i < len(fields) else '',
                'start_date': start_dates[i] if i < len(start_dates) else None,
                'end_date': end_dates[i] if i < len(end_dates) else None,
                'description': descriptions[i] if i < len(descriptions) else '',
            })
    save_education(user_id, edu_list)

    update_profile_completion(user_id)

    flash('Profile updated successfully!', 'success')
    return redirect(url_for('profile.own_profile'))


# ──────────────────────────────────────────────────────────
# View Own Profile
# ──────────────────────────────────────────────────────────

@profile_bp.route('/own', methods=['GET'])
@login_required
def own_profile():
    user_id = session['user_id']
    data = get_full_profile(user_id)

    if not data:
        flash('Please set up your profile first.', 'info')
        return redirect(url_for('profile.setup_page'))

    return render_template('profile/view.html', data=data, is_own=True, connection_status=None)


# ──────────────────────────────────────────────────────────
# View Other User's Profile
# ──────────────────────────────────────────────────────────

@profile_bp.route('/<int:user_id>', methods=['GET'])
@login_required
def view_profile(user_id):
    current_user_id = session['user_id']

    # Redirect to own profile if same user
    if user_id == current_user_id:
        return redirect(url_for('profile.own_profile'))

    data = get_full_profile(user_id)
    if not data:
        flash('User not found.', 'danger')
        return redirect(url_for('profile.own_profile'))

    # Increment visit count
    increment_visit(user_id, 'user')

    # Get connection status
    conn_status = get_connection_status(current_user_id, user_id)

    return render_template(
        'profile/view.html',
        data=data,
        is_own=False,
        connection_status=conn_status,
    )
