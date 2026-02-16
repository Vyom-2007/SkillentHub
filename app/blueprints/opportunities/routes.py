"""
Opportunities routes blueprint.
Handles browsing and viewing jobs/internships.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from functools import wraps
from app.services import opportunity_service, application_service

opportunities_bp = Blueprint('opportunities', __name__)


def login_required(f):
    """Decorator to require login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@opportunities_bp.route('/opportunities')
@login_required
def opportunities():
    """Display opportunities page with filters."""
    opp_type = request.args.get('type', 'all')
    user_id = session.get('user_id')
    
    # Get initial opportunities with match scores
    items = opportunity_service.search_opportunities(opp_type=opp_type, user_id=user_id)
    
    # Get filter options
    locations = opportunity_service.get_all_locations()
    counts = opportunity_service.get_opportunity_counts()
    
    return render_template('opportunities/opportunities.html',
                           opportunities=items,
                           locations=locations,
                           counts=counts,
                           current_type=opp_type)


@opportunities_bp.route('/api/opportunities/search')
@login_required
def search_opportunities():
    """API endpoint for searching opportunities."""
    opp_type = request.args.get('type', 'all')
    q = request.args.get('q', '').strip()
    location = request.args.get('location', '').strip()
    work_mode = request.args.get('work_mode', '').strip()
    job_type = request.args.get('job_type', '').strip()
    date_posted = request.args.get('date_posted', '').strip()
    experience = request.args.get('experience', '').strip()
    page = request.args.get('page', 1, type=int)
    user_id = session.get('user_id')
    
    results = opportunity_service.search_opportunities(
        opp_type=opp_type if opp_type else 'all',
        q=q if q else None,
        location=location if location else None,
        work_mode=work_mode if work_mode else None,
        job_type=job_type if job_type else None,
        date_posted=date_posted if date_posted else None,
        experience=experience if experience else None,
        page=page,
        user_id=user_id
    )
    
    # Format for JSON
    opportunities_json = []
    for item in results:
        opportunities_json.append({
            'id': item['id'],
            'type': item['type'],
            'title': item['title'],
            'location': item['location'],
            'company_name': item.get('company_name'),
            'work_mode': item.get('work_mode'),
            'job_type': item.get('job_type'),
            'salary_range': item.get('salary_range'),
            'stipend': item.get('stipend'),
            'duration': item.get('duration'),
            'skills_required': item.get('skills_required'),
            'posted_at': item['posted_at'].isoformat() if item.get('posted_at') else None,
            'match_score': item.get('match_score')
        })
    
    return jsonify({'success': True, 'opportunities': opportunities_json})


@opportunities_bp.route('/jobs/<int:job_id>')
@login_required
def job_detail(job_id):
    """Display job details."""
    user_id = session.get('user_id')
    job = opportunity_service.get_job_by_id(job_id)
    
    if not job:
        flash('Job not found.', 'error')
        return redirect(url_for('opportunities.opportunities'))
    
    # Check if already applied
    has_applied = application_service.has_applied(user_id, 'job', job_id)
    
    return render_template('opportunities/job_detail.html',
                           item=job,
                           item_type='job',
                           has_applied=has_applied)


@opportunities_bp.route('/internships/<int:internship_id>')
@login_required
def internship_detail(internship_id):
    """Display internship details."""
    user_id = session.get('user_id')
    internship = opportunity_service.get_internship_by_id(internship_id)
    
    if not internship:
        flash('Internship not found.', 'error')
        return redirect(url_for('opportunities.opportunities'))
    
    # Check if already applied
    has_applied = application_service.has_applied(user_id, 'internship', internship_id)
    
    return render_template('opportunities/internship_detail.html',
                           item=internship,
                           item_type='internship',
                           has_applied=has_applied)
