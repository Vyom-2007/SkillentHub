from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash
from app.models.connection import Connection
from app.services.auth_service import AuthService

connections_bp = Blueprint('connections', __name__, url_prefix='/connections')

@connections_bp.route('/requests')
def requests_page():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    requests = Connection.get_pending_requests(session['user_id'])
    return render_template('connections/requests.html', requests=requests)

from app.services.notification_service import NotificationService

@connections_bp.route('/api/request', methods=['POST'])
def send_request():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    sender_id = session['user_id']
    data = request.get_json()
    receiver_id = data.get('target_user_id')
    
    if Connection.create(sender_id, receiver_id, sender_id):
        NotificationService.create_notification(
            receiver_id, 'connection_request',
            f"{session['full_name']} sent you a connection request.", sender_id
        )
        return jsonify({'success': True})
    return jsonify({'error': 'Failed or already exists'}), 400

@connections_bp.route('/<int:conn_id>/accept', methods=['POST'])
def accept_request(conn_id):
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    
    # We need to know who sent the request to notify them
    # A bit redundant query, but robust.
    # Logic: If I accept, the other person (created_by) gets notified.
    # Connection.accept updates status. We need to fetch details first or after.
    
    # Fetch connection details to get the ORIGINAL SENDER (who created it)
    conn = get_db_connection()
    other_user_id = None
    try:
         with conn.cursor() as cursor:
             cursor.execute("SELECT created_by FROM connections WHERE connection_id = %s", (conn_id,))
             res = cursor.fetchone()
             if res: other_user_id = res['created_by']
    finally:
        conn.close()

    if Connection.accept(conn_id, session['user_id']):
         if other_user_id:
             NotificationService.create_notification(
                 other_user_id, 'connection_accepted',
                 f"{session['full_name']} accepted your connection request.", session['user_id']
             )
         flash('Connection accepted!', 'success')
    else:
         flash('Error accepting connection.', 'danger')
         
    return redirect(url_for('connections.requests_page'))

# TODO: Reject, etc.
