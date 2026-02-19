"""
Recruiter dashboard and management routes.
All routes protected by @recruiter_required decorator.
"""
from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
from app.utils.decorators import recruiter_required
from app.services import recruiter_service, recruiter_auth_service


recruiter_bp = Blueprint('recruiter', __name__, url_prefix='/recruiter')


@recruiter_bp.route('/dashboard')
@recruiter_required
def dashboard():
    """Recruiter dashboard with stats and recent activity."""
    recruiter_id = session.get('recruiter_id')
    
    # Get recruiter info
    recruiter = recruiter_auth_service.get_recruiter_by_id(recruiter_id)
    if not recruiter:
        flash('Recruiter not found', 'danger')
        return redirect(url_for('auth_recruiter.logout'))
    
    # Get dashboard stats
    stats = recruiter_service.get_dashboard_stats(recruiter_id)
    
    return render_template('recruiter/dashboard.html', 
                           recruiter=recruiter,
                           stats=stats)

# Import sub-modules to register routes
from app.blueprints.recruiter import interviews, routes_manage, routes_post, routes_settings, routes_registrations


@recruiter_bp.route('/analytics')
@recruiter_required
def analytics():
    """Recruiter analytics dashboard."""
    recruiter_id = session.get('recruiter_id')
    
    # Get stats
    from app.services import recruiter_service
    stats = recruiter_service.get_analytics_stats(recruiter_id)
    
    return render_template('recruiter/analytics.html', stats=stats)


@recruiter_bp.route('/save_candidate/<int:user_id>', methods=['POST'])
@recruiter_required
def save_candidate(user_id):
    """Save a candidate profile."""
    recruiter_id = session.get('recruiter_id')
    success, message = recruiter_service.save_candidate(recruiter_id, user_id)
    return jsonify({'success': success, 'message': message})


@recruiter_bp.route('/unsave_candidate/<int:user_id>', methods=['POST'])
@recruiter_required
def unsave_candidate(user_id):
    """Unsave a candidate profile."""
    recruiter_id = session.get('recruiter_id')
    success, message = recruiter_service.unsave_candidate(recruiter_id, user_id)
    return jsonify({'success': success, 'message': message})


@recruiter_bp.route('/saved_candidates')
@recruiter_required
def saved_candidates():
    """View saved candidates."""
    recruiter_id = session.get('recruiter_id')
    candidates = recruiter_service.get_saved_candidates(recruiter_id)
    return render_template('recruiter/saved_candidates.html', candidates=candidates)


