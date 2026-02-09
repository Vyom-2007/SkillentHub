"""
Profile management routes blueprint.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from functools import wraps
from app.services import profile_service

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
    
    # Record visit if viewing someone else's profile
    if not is_own_profile and current_user_id:
        profile_service.record_visit(user_id, current_user_id, None)
    
    # Get posts
    posts = profile_service.get_user_posts(user_id)
    
    context = {
        'profile': profile,
        'posts': posts,
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
        
        # Validation
        errors = []
        if not data['full_name']:
            errors.append('Full name is required')
        if not data['headline']:
            errors.append('Headline is required')
        if data['phone'] and (not data['phone'].isdigit() or len(data['phone']) != 10):
            errors.append('Phone must be exactly 10 digits')
        
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
        print(f"DEBUG: Received skill_ids from form: {skill_ids}")
        profile_service.update_user_skills(user_id, skill_ids)
        
        # Handle education
        education_list = parse_education_form(request.form)
        profile_service.save_education_entries(user_id, education_list)
        
        session['full_name'] = data['full_name']
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile.view', user_id=user_id))
    
    # GET
    profile = profile_service.get_profile_with_details(user_id)
    return render_template('profile/edit.html',
                           profile=profile,
                           all_skills=profile_service.get_all_skills())


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
    for i in range(len(institutions)):
        if institutions[i] and degrees[i]:
            education_list.append({
                'institution_name': institutions[i].strip(),
                'degree': degrees[i].strip(),
                'field_of_study': fields[i].strip() if i < len(fields) else '',
                'start_year': int(starts[i]) if i < len(starts) and starts[i] else None,
                'end_year': int(ends[i]) if i < len(ends) and ends[i] else None
            })
    
    return education_list
