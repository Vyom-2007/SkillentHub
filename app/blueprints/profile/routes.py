"""
Profile management routes blueprint.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from functools import wraps
from app.services import profile_service, connection_service

profile_bp = Blueprint('profile', __name__, url_prefix='/profile')


def login_required(f):
    """Decorator to require login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@profile_bp.route('/setup', methods=['GET', 'POST'])
@login_required
def setup():
    """First-time profile setup."""
    user_id = session.get('user_id')
    
    if request.method == 'POST':
        data = {
            'full_name': request.form.get('full_name', '').strip(),
            'headline': request.form.get('headline', '').strip(),
            'bio': request.form.get('bio', '').strip(),
            'location': request.form.get('location', '').strip(),
            'phone': request.form.get('phone', '').strip()
        }
        
        # Validation
        errors = []
        if not data['full_name']:
            errors.append('Full name is required')
        if not data['headline']:
            errors.append('Headline is required')
        if data['phone'] and (not data['phone'].isdigit() or len(data['phone']) != 10):
            errors.append('Phone must be exactly 10 digits')
        if data['bio'] and len(data['bio']) > 5000:
            errors.append('Bio must be less than 5000 characters')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('profile/setup.html',
                                   data=data,
                                   skills=profile_service.get_all_skills())
        
        # Handle profile picture
        profile_picture = request.files.get('profile_picture')
        
        # Check if profile exists
        if profile_service.profile_exists(user_id):
            success, message = profile_service.update_profile(user_id, data, profile_picture)
        else:
            success, message = profile_service.create_profile(user_id, data, profile_picture)
        
        if not success:
            flash(message, 'error')
            return render_template('profile/setup.html',
                                   data=data,
                                   skills=profile_service.get_all_skills())
        
        # Handle skills
        skill_ids = request.form.getlist('skills')
        profile_service.update_user_skills(user_id, skill_ids)
        
        # Handle education entries
        education_list = parse_education_form(request.form)
        profile_service.save_education_entries(user_id, education_list)
        
        # Update session
        session['full_name'] = data['full_name']
        updated_profile = profile_service.get_profile(user_id)
        if updated_profile:
            session['profile_picture'] = updated_profile.get('profile_picture')
        
        flash('Profile saved successfully!', 'success')
        return redirect(url_for('profile.view', user_id=user_id))
    
    # GET request
    existing = profile_service.get_profile(user_id)
    all_skills = profile_service.get_all_skills()
    
    return render_template('profile/setup.html',
                           data=existing or {'full_name': session.get('full_name', '')},
                           skills=all_skills,
                           user_skills=[])


@profile_bp.route('/<int:user_id>')
def view(user_id):
    """View a user's profile."""
    profile = profile_service.get_profile_with_details(user_id)
    
    if not profile:
        flash('Profile not found.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    current_user_id = session.get('user_id')
    is_own_profile = current_user_id == user_id
    
    # Privacy Check
    if profile.get('visibility') == 'private':
        # Allow if owner or connected
        is_connected = current_user_id and connection_service.are_connected(current_user_id, user_id)
        if not is_own_profile and not is_connected:
            flash('This profile is private. Connect with the user to view their profile.', 'warning')
            if current_user_id:
                # Redirect to user's own profile or network? Network seems better to find other people.
                # Or maybe back to where they came from?
                return redirect(url_for('network.network'))
            return redirect(url_for('auth.login'))
    
    # Record visit if viewing someone else's profile
    if not is_own_profile and current_user_id:
        profile_service.record_visit(user_id, current_user_id, None)
    
    # Get posts
    posts = profile_service.get_user_posts(user_id)
    
    # Get achievements/wins
    wins = profile_service.get_user_wins(user_id)
    
    context = {
        'profile': profile,
        'posts': posts,
        'wins': wins,
        'is_own_profile': is_own_profile
    }
    
    if is_own_profile:
        context['visit_stats'] = profile_service.get_visit_stats(user_id)
    
    return render_template('profile/view.html', **context)


@profile_bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    """Edit own profile."""
    user_id = session.get('user_id')
    
    if not profile_service.profile_exists(user_id):
        return redirect(url_for('profile.setup'))
    
    if request.method == 'POST':
        data = {
            'full_name': request.form.get('full_name', '').strip(),
            'headline': request.form.get('headline', '').strip(),
            'bio': request.form.get('bio', '').strip(),
            'location': request.form.get('location', '').strip(),
            'phone': request.form.get('phone', '').strip()
        }
        
        
        # Validation disabled for required fields as per request
        errors = []
        
        # Basic data processing only
        if not data['full_name']:
            # Use existing name from session or profile if available to avoid DB constraint error
            # IF the user cleared it, we might need to allow it if DB permits, 
            # but usually full_name is required. 
            pass

        if errors:
            for error in errors:
                flash(error, 'error')
            profile = profile_service.get_profile_with_details(user_id)
            return render_template('profile/edit.html',
                                   profile=profile,
                                   all_skills=profile_service.get_all_skills())
        
        # Handle profile picture
        profile_picture = request.files.get('profile_picture')
        
        success, message = profile_service.update_profile(user_id, data, profile_picture)
        
        if not success:
            flash(message, 'error')
            profile = profile_service.get_profile_with_details(user_id)
            return render_template('profile/edit.html',
                                   profile=profile,
                                   all_skills=profile_service.get_all_skills())
        
        # Handle skills
        skill_ids = request.form.getlist('skills')
        
        # Custom skills
        custom_skills = request.form.getlist('custom_skills[]')
        if custom_skills:
            for skill_name in custom_skills:
                if skill_name.strip():
                    new_skill_id = profile_service.add_skill_if_not_exists(skill_name)
                    if str(new_skill_id) not in skill_ids:
                        skill_ids.append(str(new_skill_id))
        
        # Additional privacy settings
        data['show_skills'] = 1 if request.form.get('show_skills') else 0
        data['show_education'] = 1 if request.form.get('show_education') else 0
        data['show_experience'] = 1 if request.form.get('show_experience') else 0
        data['show_resume'] = 1 if request.form.get('show_resume') else 0
        
        # Handle resume upload
        resume_file = request.files.get('resume_file')
        
        print(f"DEBUG: Received skill_ids from form: {skill_ids}")
        
        # Update profile with resume
        success, message = profile_service.update_profile(user_id, data, profile_picture, resume_file)
        
        if not success:
            flash(message, 'error')
            profile = profile_service.get_profile_with_details(user_id)
            return render_template('profile/edit.html',
                                   profile=profile,
                                   all_skills=profile_service.get_all_skills())
        
        profile_service.update_user_skills(user_id, skill_ids)
        
        # Handle education
        education_list = parse_education_form(request.form)
        profile_service.save_education_entries(user_id, education_list)
        
        session['full_name'] = data['full_name']
        updated_profile = profile_service.get_profile(user_id)
        if updated_profile:
            session['profile_picture'] = updated_profile.get('profile_picture')
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile.view', user_id=user_id))
    
    # GET
    profile = profile_service.get_profile_with_details(user_id)
    return render_template('profile/edit.html',
                           profile=profile,
                           all_skills=profile_service.get_all_skills())


@profile_bp.route('/api/parse-resume', methods=['POST'])
@login_required
def parse_resume_route():
    """Parse resume and return structured data."""
    if 'resume' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
        
    file = request.files['resume']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
        
    # Check Allowed ext
    allowed_exts = {'pdf', 'docx', 'doc', 'txt'}
    filename = file.filename
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    if ext not in allowed_exts:
        return jsonify({'error': 'File type not allowed. Use PDF or DOCX.'}), 400
    
    try:
        # Save temp file
        temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp_' + filename)
        file.save(temp_path)
        
        # Parse
        from app.utils.resume_parser import parse_resume
        data = parse_resume(temp_path)
        
        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        return jsonify(data)
        
    except Exception as e:
        current_app.logger.error(f"Error parsing resume: {e}")
        return jsonify({'error': str(e)}), 500


@profile_bp.route('/resume/<filename>')
@login_required
def download_resume(filename):
    """Download user resume."""
    from flask import send_from_directory, current_app, abort
    from app.utils.permissions import can_access_resume
    
    # Determine viewer
    viewer_id = session.get('user_id') or session.get('recruiter_id')
    viewer_role = 'recruiter' if session.get('recruiter_id') else 'user'
    
    if not viewer_id:
        # Should be covered by login_required but good for safety
        abort(401)
        
    if not can_access_resume(filename, viewer_id, viewer_role):
        abort(403)
        
    try:
        # Check profiles dir first
        # Note: logic in can_access_resume checks both profile and app resumes.
        # But where are they stored?
        # Profile resume -> static/uploads/profiles/ (maybe? or resumes/)
        # App resume -> static/uploads/resumes/
        
        # Let's check where they are actually stored.
        # application_service.save_resume -> 'static/uploads/resumes'
        # profile_service? I should check.
        # Assuming all in 'static/uploads/resumes' or we check both.
        
        # Check profile resumes first
        profile_resumes_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'profile_resumes')
        if os.path.exists(os.path.join(profile_resumes_dir, filename)):
             return send_from_directory(profile_resumes_dir, filename, as_attachment=True)

        # Check application resumes (legacy or job applications)
        app_resumes_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'resumes')
        if os.path.exists(os.path.join(app_resumes_dir, filename)):
             return send_from_directory(app_resumes_dir, filename, as_attachment=True)
        
        abort(404)
    except Exception as e:
        current_app.logger.error(f"Error serving resume: {e}")
        abort(404)


@profile_bp.route('/education/delete/<int:education_id>', methods=['POST'])
@login_required
def delete_education(education_id):
    """Delete education entry via AJAX."""
    user_id = session.get('user_id')
    profile_service.delete_education(education_id, user_id)
    return jsonify({'success': True})


def parse_education_form(form):
    """Parse education entries from form."""
    institutions = form.getlist('edu_institution[]')
    degrees = form.getlist('edu_degree[]')
    fields = form.getlist('edu_field[]')
    starts = form.getlist('edu_start[]')
    ends = form.getlist('edu_end[]')
    
    education_list = []
    # Loop over institutions as primary key
    for i in range(len(institutions)):
        # Even if empty, if user wants to save it as empty, we should allow? 
        # But usually we need at least institution/degree to make sense of a record.
        # User said "nothing compulsory" but an empty record is useless.
        # However, we will allow partial records if at least one field is filled?
        # Or just save whatever is there. 
        # Minimal check: if all fields are empty, skip.
        
        inst = institutions[i].strip()
        deg = degrees[i].strip()
        
        # If both primary fields are empty, assume it's a blank row unless other fields have data
        # But to avoid cluttering DB with empty rows, let's require at least one field to have content
        has_content = any([
            inst, deg, 
            (i < len(fields) and fields[i].strip()),
            (i < len(starts) and starts[i]),
            (i < len(ends) and ends[i])
        ])
        
        if has_content:
            education_list.append({
                'institution_name': inst,
                'degree': deg,
                'field_of_study': fields[i].strip() if i < len(fields) else '',
                'start_year': int(starts[i]) if i < len(starts) and starts[i] else None,
                'end_year': int(ends[i]) if i < len(ends) and ends[i] else None
            })
    
    return education_list
