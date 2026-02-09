"""
Network routes blueprint.
Handles user directory and search.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from functools import wraps
from app.services import network_service
from app.services import connection_service

network_bp = Blueprint('network', __name__)


def login_required(f):
    """Decorator to require login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@network_bp.route('/network')
@login_required
def network():
    """Display network page with user directory."""
    page = request.args.get('page', 1, type=int)
    user_id = session.get('user_id')
    
    # Get initial users (excluding current user)
    result = network_service.get_all_users(page=page, current_user_id=user_id)
    
    # Add connection status to each user
    for user in result['users']:
        conn = connection_service.get_connection(user_id, user['user_id'])
        if conn:
            user['connection_status'] = conn['status']
            user['connection_id'] = conn['connection_id']
            user['pending_sent_by_me'] = conn['created_by'] == user_id
        else:
            user['connection_status'] = 'none'
            user['connection_id'] = None
            user['pending_sent_by_me'] = False
    
    # Get connections and pending requests
    connections = connection_service.get_my_connections(user_id)
    pending_requests = connection_service.get_pending_requests(user_id)
    
    # Get filter options
    all_skills = network_service.get_all_skills()
    all_locations = network_service.get_all_locations()
    
    return render_template('network/network.html',
                           users=result['users'],
                           total=result['total'],
                           page=result['page'],
                           has_more=result['has_more'],
                           connections=connections,
                           pending_requests=pending_requests,
                           all_skills=all_skills,
                           all_locations=all_locations)


@network_bp.route('/api/users/search')
@login_required
def search_users():
    """Search users API endpoint."""
    q = request.args.get('q', '').strip()
    skills = request.args.get('skills', '').strip()
    location = request.args.get('location', '').strip()
    page = request.args.get('page', 1, type=int)
    user_id = session.get('user_id')
    
    result = network_service.search_users(
        q=q if q else None,
        skills=skills if skills else None,
        location=location if location else None,
        page=page,
        current_user_id=user_id
    )
    
    # Format users for JSON response with connection status
    users_json = []
    for user in result['users']:
        conn = connection_service.get_connection(user_id, user['user_id'])
        conn_status = 'none'
        conn_id = None
        pending_sent_by_me = False
        if conn:
            conn_status = conn['status']
            conn_id = conn['connection_id']
            pending_sent_by_me = conn['created_by'] == user_id
        
        users_json.append({
            'user_id': user['user_id'],
            'full_name': user['full_name'] or 'User',
            'headline': user['headline'],
            'location': user['location'],
            'profile_picture': user['profile_picture'],
            'skills': [s['skill_name'] for s in user.get('skills', [])],
            'connection_status': conn_status,
            'connection_id': conn_id,
            'pending_sent_by_me': pending_sent_by_me
        })
    
    return jsonify({
        'success': True,
        'users': users_json,
        'total': result['total'],
        'page': result['page'],
        'has_more': result['has_more']
    })

