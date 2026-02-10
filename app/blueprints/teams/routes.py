from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.models.team import Team
from app.services.auth_service import AuthService
from app.services.notification_service import NotificationService
from database.connection import get_db_connection

teams_bp = Blueprint('teams', __name__, url_prefix='/teams')

@teams_bp.route('/')
def index():
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    
    my_teams = Team.get_user_teams(session['user_id'])
    return render_template('teams/index.html', teams=my_teams)

@teams_bp.route('/create', methods=['GET', 'POST'])
def create_team():
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        name = request.form.get('team_name')
        event_name = request.form.get('event_name')
        
        team_id = Team.create(name, event_name, session['user_id'])
        if team_id:
            flash('Team created successfully!', 'success')
            return redirect(url_for('teams.view_team', team_id=team_id))
        else:
            flash('Error creating team.', 'danger')
            
    return render_template('teams/create.html')

@teams_bp.route('/<int:team_id>')
def view_team(team_id):
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    
    team = Team.get_by_id(team_id)
    if not team: return redirect(url_for('teams.index'))
    
    members = Team.get_members(team_id)
    is_member = any(m['user_id'] == session['user_id'] for m in members)
    
    return render_template('teams/view.html', team=team, members=members, is_member=is_member)

@teams_bp.route('/<int:team_id>/invite', methods=['POST'])
def invite_member(team_id):
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    
    email = request.form.get('email')
    result = Team.invite_member(team_id, session['user_id'], email)
    
    if result == 'success':
        # Need to find invited_user_id to send notification
        conn = get_db_connection()
        try:
             with conn.cursor() as cursor:
                 cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
                 user = cursor.fetchone()
                 if user:
                     NotificationService.create_notification(
                         user['user_id'], 'team_invitation',
                         f"{session['full_name']} invited you to join team.", team_id
                     )
        finally:
             conn.close()
             
        flash('Invitation sent!', 'success')
    elif result == 'user_not_found':
        flash('User not found.', 'warning')
    elif result == 'already_member':
        flash('User is already a member.', 'info')
    else:
        flash('Error sending invitation.', 'danger')
        
    return redirect(url_for('teams.view_team', team_id=team_id))
