"""
Hackathons routes.
Handles hackathon browsing, details, and registration.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from functools import wraps
from app.services import event_service
from datetime import datetime

hackathons_bp = Blueprint('hackathons', __name__)


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


@hackathons_bp.route('/hackathons')
@login_required
def hackathons_list():
    """Display list of hackathons."""
    page = request.args.get('page', 1, type=int)
    hackathons = event_service.get_hackathons(page=page)
    counts = event_service.get_event_counts()
    
    return render_template('opportunities/hackathons_list.html',
                           events=hackathons,
                           counts=counts,
                           event_type='hackathon')


@hackathons_bp.route('/hackathons/<int:hackathon_id>')
@login_required
def hackathon_detail(hackathon_id):
    """Display hackathon details."""
    user_id = session.get('user_id')
    hackathon = event_service.get_hackathon_by_id(hackathon_id)
    
    if not hackathon:
        flash('Hackathon not found.', 'error')
        return redirect(url_for('hackathons.hackathons_list'))
    
    is_registered = event_service.is_registered_hackathon(hackathon_id, user_id)
    
    return render_template('opportunities/hackathon_detail.html',
                           event=hackathon,
                           event_type='hackathon',
                           is_registered=is_registered,
                           now=datetime.now())


@hackathons_bp.route('/hackathons/<int:hackathon_id>/register', methods=['POST'])
@api_login_required
def register_hackathon(hackathon_id):
    """Register for a hackathon."""
    user_id = session.get('user_id')
    team_name = None
    members = []
    
    if request.is_json:
        team_name = request.json.get('team_name')
        members = request.json.get('members', [])
    
    success, result = event_service.register_hackathon(hackathon_id, user_id, team_name, members)
    
    if success:
        return jsonify({'success': True, 'registration_id': result})
    else:
        return jsonify({'error': result}), 400


@hackathons_bp.route('/events/registrations')
@login_required
def my_registrations():
    """Display user's event registrations."""
    user_id = session.get('user_id')
    event_type = request.args.get('type', '').strip()
    
    registrations = event_service.get_user_registrations(
        user_id,
        event_type=event_type if event_type else None
    )
    
    return render_template('applications/my_registrations.html',
                           registrations=registrations,
                           current_type=event_type)
