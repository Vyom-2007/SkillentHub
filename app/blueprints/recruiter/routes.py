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


