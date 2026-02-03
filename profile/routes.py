"""
User profile routes blueprint.
"""

import os
import time
from functools import wraps

from flask import Blueprint, render_template, redirect, url_for, flash, session, request, abort, current_app
from werkzeug.utils import secure_filename

from database.db import execute_query
from profile.forms import EditProfileForm


# Create the profile blueprint
profile_bp = Blueprint('profile', __name__, url_prefix='/profile')


def login_required(f):
    """
    Decorator to require user login for protected routes.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def get_unique_filename(original_filename, user_id, prefix=''):
    """
    Generate a unique filename by appending user_id and timestamp.
    
    Args:
        original_filename (str): The original uploaded filename.
        user_id (int): The user's ID.
        prefix (str): Optional prefix for the filename.
    
    Returns:
        str: A unique, secure filename.
    """
    # Secure the filename to prevent directory traversal attacks
    filename = secure_filename(original_filename)
    
    # Split filename and extension
    name, ext = os.path.splitext(filename)
    
    # Generate unique filename with user_id and timestamp
    timestamp = int(time.time())
    unique_filename = f"{prefix}{user_id}_{timestamp}{ext}"
    
    return unique_filename


def save_uploaded_file(file, subfolder, user_id, prefix=''):
    """
    Save an uploaded file to the specified subfolder.
    
    Args:
        file: The uploaded file object.
        subfolder (str): Subfolder within UPLOAD_FOLDER (e.g., 'profiles', 'resumes').
        user_id (int): The user's ID for unique filename generation.
        prefix (str): Optional prefix for the filename.
    
    Returns:
        str: The saved filename, or None if no file was uploaded.
    """
    if file and file.filename:
        # Get unique filename
        filename = get_unique_filename(file.filename, user_id, prefix)
        
        # Ensure upload directory exists
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save the file
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        return filename
    
    return None


from connections.routes import get_connection_status

@profile_bp.route('/view/<int:user_id>', methods=['GET'])
def view_profile(user_id):
    """
    View a user's profile.
    
    Args:
        user_id (int): The ID of the user whose profile to view.
    """
    # Fetch user data from database
    user = execute_query(
        """
        SELECT id, full_name, email, bio, education, skills, 
               github_link, linkedin_link, profile_pic, resume_file, role
        FROM users 
        WHERE id = %s
        """,
        (user_id,),
        fetch_one=True
    )
    
    if not user:
        abort(404, description="User not found")
    
    # Check if viewing own profile
    current_user_id = session.get('user_id')
    is_own_profile = current_user_id == user_id
    
    # Get connection status
    connection_status = None
    if current_user_id and not is_own_profile:
        connection_status = get_connection_status(current_user_id, user_id)
    
    return render_template(
        'profile/view_profile.html', 
        user=user, 
        is_own_profile=is_own_profile,
        connection_status=connection_status
    )


@profile_bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """
    Edit the current user's profile.
    - GET: Display form pre-filled with current data.
    - POST: Validate and update profile data.
    """
    user_id = session['user_id']
    
    # Fetch current user data
    user = execute_query(
        """
        SELECT id, full_name, email, bio, education, skills, 
               github_link, linkedin_link, profile_pic, resume_file
        FROM users 
        WHERE id = %s
        """,
        (user_id,),
        fetch_one=True
    )
    
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    form = EditProfileForm()
    
    if request.method == 'GET':
        # Pre-fill form with current data
        form.bio.data = user.get('bio', '')
        form.education.data = user.get('education', '')
        form.skills.data = user.get('skills', '')
        form.github_link.data = user.get('github_link', '')
        form.linkedin_link.data = user.get('linkedin_link', '')
    
    if form.validate_on_submit():
        # Get form data
        bio = form.bio.data.strip() if form.bio.data else None
        education = form.education.data.strip() if form.education.data else None
        skills = form.skills.data.strip() if form.skills.data else None
        github_link = form.github_link.data.strip() if form.github_link.data else None
        linkedin_link = form.linkedin_link.data.strip() if form.linkedin_link.data else None
        
        # Handle profile picture upload
        profile_pic_filename = user.get('profile_pic')  # Keep existing if no new upload
        if form.profile_pic.data and form.profile_pic.data.filename:
            new_pic = save_uploaded_file(
                form.profile_pic.data, 
                'profiles', 
                user_id, 
                prefix='profile_'
            )
            if new_pic:
                # Optionally delete old profile picture
                if profile_pic_filename:
                    old_pic_path = os.path.join(
                        current_app.config['UPLOAD_FOLDER'], 
                        'profiles', 
                        profile_pic_filename
                    )
                    if os.path.exists(old_pic_path):
                        try:
                            os.remove(old_pic_path)
                        except OSError:
                            pass  # Ignore deletion errors
                
                profile_pic_filename = new_pic
        
        # Handle resume upload
        resume_filename = user.get('resume_file')  # Keep existing if no new upload
        if form.resume.data and form.resume.data.filename:
            new_resume = save_uploaded_file(
                form.resume.data, 
                'resumes', 
                user_id, 
                prefix='resume_'
            )
            if new_resume:
                # Optionally delete old resume
                if resume_filename:
                    old_resume_path = os.path.join(
                        current_app.config['UPLOAD_FOLDER'], 
                        'resumes', 
                        resume_filename
                    )
                    if os.path.exists(old_resume_path):
                        try:
                            os.remove(old_resume_path)
                        except OSError:
                            pass  # Ignore deletion errors
                
                resume_filename = new_resume
        
        # Update user profile in database
        result = execute_query(
            """
            UPDATE users 
            SET bio = %s, 
                education = %s, 
                skills = %s, 
                github_link = %s, 
                linkedin_link = %s, 
                profile_pic = %s, 
                resume_file = %s
            WHERE id = %s
            """,
            (bio, education, skills, github_link, linkedin_link, 
             profile_pic_filename, resume_filename, user_id),
            commit=True
        )
        
        if result is not None:
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile.view_profile', user_id=user_id))
        else:
            flash('An error occurred while updating your profile. Please try again.', 'danger')
    
    return render_template(
        'profile/edit_profile.html', 
        form=form, 
        user=user
    )


@profile_bp.errorhandler(404)
def profile_not_found(error):
    """Handle 404 errors for profile routes."""
    return render_template('errors/404.html', message="User profile not found."), 404
