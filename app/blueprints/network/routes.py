from flask import Blueprint, render_template, request, jsonify, session, flash
from app.services.auth_service import AuthService
from database.connection import get_db_connection

network_bp = Blueprint('network', __name__, url_prefix='/network')

@network_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    user_id = session['user_id']
    
    # Simple search or get all users excluding self
    # This should be in a Service but putting here for speed in prototype
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Get all users not self
            # In a real app, this needs pagination and smarter loading
            sql = """
                SELECT u.user_id, u.full_name, p.headline, p.profile_picture,
                (SELECT COUNT(*) FROM connections c 
                 WHERE (c.user_id_1 = %s AND c.user_id_2 = u.user_id) 
                    OR (c.user_id_1 = u.user_id AND c.user_id_2 = %s)
                 AND c.status = 'accepted') as is_connected,
                 (SELECT status FROM connections c 
                 WHERE (c.user_id_1 = %s AND c.user_id_2 = u.user_id) 
                    OR (c.user_id_1 = u.user_id AND c.user_id_2 = %s)) as connection_status
                FROM users u
                LEFT JOIN profiles p ON u.user_id = p.user_id
                WHERE u.user_id != %s
                LIMIT 50
            """
            cursor.execute(sql, (user_id, user_id, user_id, user_id, user_id))
            users = cursor.fetchall()
            
            return render_template('network/index.html', users=users, user={'full_name': session['full_name']})
    finally:
        conn.close()

# More connection routes to follow...
