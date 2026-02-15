"""
Teams routes blueprint.
Handles team creation, management, invitations, and registration.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from functools import wraps
from app.services import team_service

teams_bp = Blueprint('teams', __name__)


def api_login_required(f):
    """Decorator for API endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function


def login_required(f):
    """Decorator for page routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


# ========== PAGE ROUTES ==========

@teams_bp.route('/teams')
@login_required
def my_teams():
    """List user's teams."""
    user_id = session.get('user_id')
    teams = team_service.get_my_teams(user_id)
    invitations = team_service.get_user_invitations(user_id)
    
    return render_template('teams/my_teams.html',
                           teams=teams,
                           invitations=invitations)


@teams_bp.route('/teams/create')
@login_required
def create_team_page():
    """Create team page."""
    item_type = request.args.get('type', 'competition')
    item_id = request.args.get('id', type=int)
    
    # Get event info
    event = None
    if item_type and item_id:
        from app.database.connection import execute_query
        if item_type == 'competition':
            event = execute_query(
                "SELECT competition_id as id, title, team_size_min, team_size_max FROM competitions WHERE competition_id = %s",
                (item_id,), fetch_one=True
            )
        else:
            event = execute_query(
                "SELECT hackathon_id as id, title, team_size_min, team_size_max FROM hackathons WHERE hackathon_id = %s",
                (item_id,), fetch_one=True
            )
    
    return render_template('teams/create_team.html',
                           item_type=item_type,
                           item_id=item_id,
                           event=event)


@teams_bp.route('/teams/<int:team_id>')
@login_required
def team_detail(team_id):
    """Team detail/management page."""
    user_id = session.get('user_id')
    team = team_service.get_team_details(team_id)
    
    if not team:
        flash('Team not found.', 'error')
        return redirect(url_for('teams.my_teams'))
    
    # Check if user is member
    is_member = any(m['user_id'] == user_id for m in team['members'])
    is_leader = team['created_by'] == user_id
    
    # Get connectable users for invite
    connectable_users = []
    if is_leader:
        connectable_users = team_service.get_connectable_users(user_id, team_id)
    
    # Get event info
    from app.database.connection import execute_query
    event = None
    if team['item_type'] == 'competition':
        event = execute_query(
            "SELECT competition_id as id, title, team_size_min, team_size_max FROM competitions WHERE competition_id = %s",
            (team['item_id'],), fetch_one=True
        )
    else:
        event = execute_query(
            "SELECT hackathon_id as id, title, team_size_min, team_size_max FROM hackathons WHERE hackathon_id = %s",
            (team['item_id'],), fetch_one=True
        )
    
    # Check if can register
    can_register = False
    if is_leader and not team['is_registered']:
        min_size = event.get('team_size_min', 1) if event else 1
        max_size = event.get('team_size_max') if event else None
        member_count = len(team['members'])
        can_register = member_count >= min_size and (max_size is None or member_count <= max_size)
    
    return render_template('teams/team_detail.html',
                           team=team,
                           event=event,
                           is_member=is_member,
                           is_leader=is_leader,
                           connectable_users=connectable_users,
                           can_register=can_register)


# ========== API ENDPOINTS ==========

@teams_bp.route('/api/teams/create', methods=['POST'])
@api_login_required
def create_team():
    """Create a new team."""
    user_id = session.get('user_id')
    data = request.get_json() or {}
    
    team_name = data.get('team_name', '').strip()
    item_type = data.get('item_type')
    item_id = data.get('item_id')
    
    if not team_name:
        return jsonify({'error': 'Team name required'}), 400
    if not item_type or not item_id:
        return jsonify({'error': 'Event selection required'}), 400
    if item_type not in ['competition', 'hackathon']:
        return jsonify({'error': 'Invalid event type'}), 400
    
    team_id, error = team_service.create_team(user_id, team_name, item_type, item_id)
    
    if team_id:
        return jsonify({'success': True, 'team_id': team_id})
    return jsonify({'error': error}), 400


@teams_bp.route('/api/teams/mine')
@api_login_required
def get_my_teams():
    """Get user's teams."""
    user_id = session.get('user_id')
    teams = team_service.get_my_teams(user_id)
    
    return jsonify({
        'teams': [{
            'team_id': t['team_id'],
            'team_name': t['team_name'],
            'item_type': t['item_type'],
            'item_id': t['item_id'],
            'role': t['role'],
            'member_count': t['member_count']
        } for t in teams]
    })


@teams_bp.route('/api/teams/<int:team_id>')
@api_login_required
def get_team(team_id):
    """Get team details."""
    team = team_service.get_team_details(team_id)
    if not team:
        return jsonify({'error': 'Team not found'}), 404
    
    return jsonify({
        'team_id': team['team_id'],
        'team_name': team['team_name'],
        'item_type': team['item_type'],
        'is_registered': team['is_registered'],
        'members': [{
            'user_id': m['user_id'],
            'full_name': m['full_name'],
            'role': m['role']
        } for m in team['members']]
    })


@teams_bp.route('/api/teams/<int:team_id>/invite', methods=['POST'])
@api_login_required
def invite_member(team_id):
    """Invite a user to team."""
    user_id = session.get('user_id')
    data = request.get_json() or {}
    target_user_id = data.get('user_id')
    
    if not target_user_id:
        return jsonify({'error': 'User ID required'}), 400
    
    success, result = team_service.invite_member(user_id, team_id, target_user_id)
    
    if success:
        return jsonify({'success': True, 'invitation_id': result})
    return jsonify({'error': result}), 400


@teams_bp.route('/api/teams/<int:team_id>/invite-by-email', methods=['POST'])
@api_login_required
def invite_member_by_email(team_id):
    """Invite a user to team by email."""
    user_id = session.get('user_id')
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    name = data.get('name', '').strip() # Optional, for UI validation if we wanted
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    success, result = team_service.invite_by_email(user_id, team_id, email, name)
    
    if success:
        return jsonify({'success': True, 'message': result})
    return jsonify({'error': result}), 400


@teams_bp.route('/api/teams/<int:team_id>/unregister', methods=['POST'])
@api_login_required
def unregister_team(team_id):
    """Unregister/Cancel team registration for event."""
    user_id = session.get('user_id')
    success, result = team_service.unregister_team(user_id, team_id)
    
    if success:
        return jsonify({'success': True, 'message': result})
    return jsonify({'error': result}), 400


@teams_bp.route('/api/teams/invitations/received')
@api_login_required
def get_invitations():
    """Get pending invitations."""
    user_id = session.get('user_id')
    invitations = team_service.get_user_invitations(user_id)
    
    return jsonify({
        'invitations': [{
            'invitation_id': i['invitation_id'],
            'team_id': i['team_id'],
            'team_name': i['team_name'],
            'item_type': i['item_type'],
            'invited_by_name': i['invited_by_name']
        } for i in invitations]
    })


@teams_bp.route('/api/teams/invitations/<int:invitation_id>/accept', methods=['PUT', 'POST'])
@api_login_required
def accept_invitation(invitation_id):
    """Accept team invitation."""
    user_id = session.get('user_id')
    success, result = team_service.accept_invitation(user_id, invitation_id)
    
    if success:
        return jsonify({'success': True, 'message': result})
    return jsonify({'error': result}), 400


@teams_bp.route('/api/teams/invitations/<int:invitation_id>/reject', methods=['PUT', 'POST'])
@api_login_required
def reject_invitation(invitation_id):
    """Reject team invitation."""
    user_id = session.get('user_id')
    success, result = team_service.reject_invitation(user_id, invitation_id)
    
    if success:
        return jsonify({'success': True, 'message': result})
    return jsonify({'error': result}), 400


@teams_bp.route('/api/teams/<int:team_id>/leave', methods=['DELETE', 'POST'])
@api_login_required
def leave_team(team_id):
    """Leave a team."""
    user_id = session.get('user_id')
    success, result = team_service.leave_team(user_id, team_id)
    
    if success:
        return jsonify({'success': True, 'message': result})
    return jsonify({'error': result}), 400


@teams_bp.route('/api/teams/<int:team_id>/members/<int:target_user_id>', methods=['DELETE', 'POST'])
@api_login_required
def remove_member(team_id, target_user_id):
    """Remove member from team."""
    user_id = session.get('user_id')
    success, result = team_service.remove_member(user_id, team_id, target_user_id)
    
    if success:
        return jsonify({'success': True, 'message': result})
    return jsonify({'error': result}), 400


@teams_bp.route('/api/teams/<int:team_id>/register', methods=['POST'])
@api_login_required
def register_team(team_id):
    """Register team for event."""
    user_id = session.get('user_id')
    success, result = team_service.register_team_for_event(user_id, team_id)
    
    if success:
        return jsonify({'success': True, 'message': result})
    return jsonify({'error': result}), 400


@teams_bp.route('/api/teams/<int:team_id>/connectable-users')
@api_login_required
def get_connectable_users(team_id):
    """Get users that can be invited."""
    user_id = session.get('user_id')
    users = team_service.get_connectable_users(user_id, team_id)
    
    return jsonify({
        'users': [{
            'user_id': u['user_id'],
            'full_name': u['full_name'],
            'headline': u['headline'],
            'profile_picture': u['profile_picture']
        } for u in users]
    })
