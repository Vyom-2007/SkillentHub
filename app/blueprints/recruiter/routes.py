"""
Recruiter dashboard and management routes.
All routes protected by @recruiter_required decorator.
"""
from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
from app.utils.decorators import recruiter_required
from app.services import recruiter_service
from app.models import recruiter as recruiter_model

recruiter_bp = Blueprint('recruiter', __name__, url_prefix='/recruiter')


@recruiter_bp.route('/dashboard')
@recruiter_required
def dashboard():
    """Recruiter dashboard with stats and recent activity."""
    recruiter_id = session.get('recruiter_id')
    
    # Get recruiter info
    recruiter = recruiter_model.get_by_id(recruiter_id)
    if not recruiter:
        flash('Recruiter not found', 'danger')
        return redirect(url_for('auth_recruiter.logout'))
    
    # Get dashboard stats
    stats = recruiter_service.get_dashboard_stats(recruiter_id)
    
    return render_template('recruiter/dashboard.html', 
                           recruiter=recruiter,
                           stats=stats)


@recruiter_bp.route('/applications')
@recruiter_required
def applications():
    """View all applications for recruiter's postings."""
    recruiter_id = session.get('recruiter_id')
    
    # Filters
    status = request.args.get('status')
    item_type = request.args.get('type')
    page = request.args.get('page', 1, type=int)
    
    applications = recruiter_service.get_all_applications(
        recruiter_id, 
        status=status, 
        item_type=item_type, 
        page=page
    )
    
    return render_template('recruiter/applications.html', 
                           applications=applications,
                           current_status=status,
                           current_type=item_type,
                           page=page)


@recruiter_bp.route('/applications/<int:application_id>/status', methods=['POST'])
@recruiter_required
def update_application_status(application_id):
    """Update application status (API endpoint)."""
    recruiter_id = session.get('recruiter_id')
    new_status = request.json.get('status')
    
    if not new_status:
        return jsonify({'success': False, 'error': 'Status required'}), 400
    
    valid_statuses = ['pending', 'reviewed', 'shortlisted', 'rejected', 'accepted']
    if new_status not in valid_statuses:
        return jsonify({'success': False, 'error': 'Invalid status'}), 400
    
    success, message = recruiter_service.update_application_status(
        application_id, new_status, recruiter_id
    )
    
    if success:
        return jsonify({'success': True, 'message': message})
    return jsonify({'success': False, 'error': message}), 400
