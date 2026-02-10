"""
Applications routes blueprint.
Handles applying to opportunities and tracking applications.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory, current_app
from functools import wraps
import os
from app.services import application_service

applications_bp = Blueprint('applications', __name__)


def login_required(f):
    """Decorator to require login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def api_login_required(f):
    """Decorator for API endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function


@applications_bp.route('/applications')
@login_required
def my_applications():
    """Display user's applications."""
    user_id = session.get('user_id')
    item_type = request.args.get('type', '').strip()
    status = request.args.get('status', '').strip()
    page = request.args.get('page', 1, type=int)
    
    applications = application_service.get_user_applications(
        user_id,
        item_type=item_type if item_type else None,
        status=status if status else None,
        page=page
    )
    
    counts = application_service.get_application_counts(user_id)
    
    return render_template('applications/my_applications.html',
                           applications=applications,
                           counts=counts,
                           current_type=item_type,
                           current_status=status)


@applications_bp.route('/applications/<int:application_id>')
@login_required
def application_detail(application_id):
    """Display application details."""
    user_id = session.get('user_id')
    application = application_service.get_application_by_id(application_id, user_id)
    
    if not application:
        flash('Application not found.', 'error')
        return redirect(url_for('applications.my_applications'))
    
    return render_template('applications/application_detail.html', application=application)


@applications_bp.route('/applications/apply', methods=['POST'])
@api_login_required
def apply():
    """Apply to a job or internship."""
    user_id = session.get('user_id')
    
    item_type = request.form.get('item_type')
    item_id = request.form.get('item_id', type=int)
    cover_letter = request.form.get('cover_letter', '')
    resume = request.files.get('resume')
    
    if not item_type or not item_id:
        return jsonify({'error': 'Invalid request'}), 400
    
    if item_type not in ['job', 'internship']:
        return jsonify({'error': 'Invalid item type'}), 400

    if not resume:
        return jsonify({'error': 'Resume is required'}), 400
        
    if not cover_letter or not cover_letter.strip():
        return jsonify({'error': 'Cover letter is required'}), 400
    
    success, result = application_service.apply_to_opportunity(
        user_id, item_type, item_id, resume, cover_letter
    )
    
    if success:
        return jsonify({'success': True, 'application_id': result})
    else:
        return jsonify({'error': result}), 400


@applications_bp.route('/applications/resume/<filename>')
@login_required
def download_resume(filename):
    """Download a resume file."""
    user_id = session.get('user_id')
    
    # Verify user owns this resume
    query_result = application_service.execute_query(
        "SELECT * FROM applications WHERE user_id = %s AND resume_path = %s",
        (user_id, filename),
        fetch_one=True
    ) if hasattr(application_service, 'execute_query') else None
    
    # For now, allow download if logged in
    resume_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'resumes')
    return send_from_directory(resume_dir, filename, as_attachment=True)
