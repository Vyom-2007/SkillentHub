from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify, current_app
from app.database.connection import execute_query
from app.utils.decorators import recruiter_required
from app.services import profile_service

candidates_bp = Blueprint('recruiter_candidates', __name__)

@candidates_bp.route('/recruiter/candidates')
@recruiter_required
def list_candidates():
    """List candidates with filtering."""
    # Filters
    search_query = request.args.get('q', '')
    skill_filter = request.args.get('skill', '')
    location_filter = request.args.get('location', '')
    
    # Base Query
    sql = """
        SELECT DISTINCT p.user_id, p.full_name, p.headline, p.profile_picture, p.location,
               (SELECT GROUP_CONCAT(s.skill_name SEPARATOR ', ') 
                FROM user_skills us 
                JOIN skills s ON us.skill_id = s.skill_id 
                WHERE us.user_id = p.user_id) as skills
        FROM profiles p
        LEFT JOIN user_skills us ON p.user_id = us.user_id
        LEFT JOIN skills s ON us.skill_id = s.skill_id
        WHERE p.visibility = 'public'
    """
    
    params = []
    
    if search_query:
        sql += " AND (p.full_name LIKE %s OR p.headline LIKE %s)"
        params.extend([f"%{search_query}%", f"%{search_query}%"])
        
    if location_filter:
        sql += " AND p.location LIKE %s"
        params.append(f"%{location_filter}%")
        
    if skill_filter:
        sql += " AND s.skill_name LIKE %s"
        params.append(f"%{skill_filter}%")
        
    sql += " GROUP BY p.user_id"
    
    candidates = execute_query(sql, tuple(params), fetch_all=True) or []
    
    return render_template('recruiter/candidates/list.html', candidates=candidates)

@candidates_bp.route('/recruiter/candidates/<int:user_id>')
@recruiter_required
def view_candidate(user_id):
    """View candidate profile."""
    try:
        # Get profile
        try:
            profile = execute_query("""
                SELECT p.*, u.email 
                FROM profiles p 
                JOIN users u ON p.user_id = u.user_id 
                WHERE p.user_id = %s
            """, (user_id,), fetch_one=True)
            if not profile:
                flash('Candidate not found', 'danger')
                return redirect(url_for('recruiter_candidates.list_candidates'))
        except Exception as e:
            current_app.logger.error(f"Error fetching profile for user {user_id}: {e}")
            raise e

        # Get skills
        try:
            skills = execute_query("""
                SELECT s.skill_name, us.proficiency_level 
                FROM user_skills us 
                JOIN skills s ON us.skill_id = s.skill_id 
                WHERE us.user_id = %s
            """, (user_id,), fetch_all=True)
        except Exception as e:
            current_app.logger.error(f"Error fetching skills for user {user_id}: {e}")
            skills = [] # Graceful degradation

        # Get experience
        try:
            experience = execute_query("SELECT * FROM experience WHERE user_id = %s ORDER BY start_date DESC", (user_id,), fetch_all=True)
        except Exception as e:
            current_app.logger.error(f"Error fetching experience for user {user_id}: {e}")
            experience = [] # Graceful degradation
        
        # Get education
        try:
            education = execute_query("SELECT * FROM education WHERE user_id = %s ORDER BY start_year DESC", (user_id,), fetch_all=True)
        except Exception as e:
            current_app.logger.error(f"Error fetching education for user {user_id}: {e}")
            education = [] # Graceful degradation
        
        # Get wins/achievements
        try:
            wins = profile_service.get_user_wins(user_id)
        except Exception as e:
            current_app.logger.error(f"Error fetching wins for user {user_id}: {e}")
            wins = []

        # Record Visit
        try:
            recruiter_id = session.get('recruiter_id')
            if recruiter_id:
                profile_service.record_visit(user_id, visitor_recruiter_id=recruiter_id)
        except Exception as e:
            current_app.logger.error(f"Error recording visit for user {user_id}: {e}")

        return render_template('recruiter/candidates/detail.html', 
                               profile=profile, 
                               skills=skills, 
                               experience=experience, 
                               education=education,
                               wins=wins)
    except Exception as e:
        current_app.logger.error(f"Critical error in view_candidate for user {user_id}: {e}")
        flash(f'Error viewing profile: {str(e)}', 'danger')
        return redirect(url_for('recruiter.dashboard'))

@candidates_bp.route('/recruiter/api/messages/send', methods=['POST'])
@recruiter_required # Checks session['recruiter_id']
def send_message_api():
    """Send message from recruiter to candidate."""
    from app.services import message_service
    recruiter_id = session.get('recruiter_id')
    
    data = request.get_json()
    receiver_id = data.get('receiver_id')
    content = data.get('content')
    
    if not receiver_id:
        return jsonify({'success': False, 'error': 'Receiver ID required'}), 400
        
    # Send message: Recruiter -> User
    msg, error = message_service.send_message(
        sender_id=recruiter_id, 
        receiver_id=receiver_id, 
        content=content, 
        sender_type='recruiter', 
        receiver_type='user' # Candidates are users
    )
    
    if error:
        return jsonify({'success': False, 'error': error}), 400
        
    return jsonify({'success': True})
