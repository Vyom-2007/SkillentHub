"""
Competitions routes.
Handles competition browsing, details, and registration.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from functools import wraps
from app.services import event_service

competitions_bp = Blueprint('competitions', __name__)


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


@competitions_bp.route('/competitions')
@login_required
def competitions_list():
    """Display list of competitions."""
    page = request.args.get('page', 1, type=int)
    competitions = event_service.get_competitions(page=page)
    counts = event_service.get_event_counts()
    
    return render_template('opportunities/competitions_list.html',
                           events=competitions,
                           counts=counts,
                           event_type='competition')


@competitions_bp.route('/competitions/<int:competition_id>')
@login_required
def competition_detail(competition_id):
    """Display competition details."""
    user_id = session.get('user_id')
    competition = event_service.get_competition_by_id(competition_id)
    
    if not competition:
        flash('Competition not found.', 'error')
        return redirect(url_for('competitions.competitions_list'))
    
    is_registered = event_service.is_registered_competition(competition_id, user_id)
    
    return render_template('opportunities/competition_detail.html',
                           event=competition,
                           event_type='competition',
                           is_registered=is_registered)


@competitions_bp.route('/competitions/<int:competition_id>/register', methods=['POST'])
@api_login_required
def register_competition(competition_id):
    """Register for a competition."""
    user_id = session.get('user_id')
    
    success, result = event_service.register_competition(competition_id, user_id)
    
    if success:
        return jsonify({'success': True, 'registration_id': result})
    else:
        return jsonify({'error': result}), 400
