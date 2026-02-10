"""
Connections routes.
Handles connection request API endpoints.
"""
from flask import Blueprint, request, session, jsonify
from functools import wraps
from app.services import connection_service

connections_bp = Blueprint('connections', __name__)


def api_login_required(f):
    """Decorator to require login for API endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function


@connections_bp.route('/api/connections/request', methods=['POST'])
@api_login_required
def send_request():
    """Send a connection request."""
    user_id = session.get('user_id')
    data = request.get_json() or {}
    to_user_id = data.get('user_id')
    
    if not to_user_id:
        return jsonify({'error': 'User ID required'}), 400
    
    success, result = connection_service.send_request(user_id, to_user_id)
    
    if success:
        return jsonify({'success': True, 'message': 'Request sent'})
    return jsonify({'error': result}), 400


@connections_bp.route('/api/connections/accept/<int:connection_id>', methods=['POST'])
@api_login_required
def accept_request(connection_id):
    """Accept a connection request."""
    user_id = session.get('user_id')
    success, result = connection_service.accept_request(connection_id, user_id)
    
    if success:
        return jsonify({'success': True, 'message': result})
    return jsonify({'error': result}), 400


@connections_bp.route('/api/connections/reject/<int:connection_id>', methods=['POST'])
@api_login_required
def reject_request(connection_id):
    """Reject a connection request."""
    user_id = session.get('user_id')
    success, result = connection_service.reject_request(connection_id, user_id)
    
    if success:
        return jsonify({'success': True, 'message': result})
    return jsonify({'error': result}), 400


@connections_bp.route('/api/connections/status/<int:user_id>')
@api_login_required
def get_status(user_id):
    """Get connection status with a user."""
    my_id = session.get('user_id')
    status = connection_service.get_connection_status(my_id, user_id)
    
    # Also check who sent the request if pending
    pending_info = None
    if status == 'pending':
        connection = connection_service.get_connection(my_id, user_id)
        if connection:
            pending_info = {
                'connection_id': connection['connection_id'],
                'sent_by_me': connection['created_by'] == my_id
            }
    
    return jsonify({
        'status': status,
        'pending_info': pending_info
    })


@connections_bp.route('/api/connections/requests')
@api_login_required
def get_requests():
    """Get incoming connection requests."""
    user_id = session.get('user_id')
    requests = connection_service.get_pending_requests(user_id)
    
    return jsonify({
        'requests': [{
            'connection_id': r['connection_id'],
            'user_id': r['user_id'],
            'full_name': r['full_name'],
            'headline': r['headline'],
            'profile_picture': r['profile_picture'],
            'requested_at': r['requested_at'].isoformat() if r['requested_at'] else None
        } for r in requests]
    })


@connections_bp.route('/api/connections/list')
@api_login_required
def get_connections():
    """Get list of connections."""
    user_id = session.get('user_id')
    connections = connection_service.get_my_connections(user_id)
    
    return jsonify({
        'connections': [{
            'connection_id': c['connection_id'],
            'user_id': c['connected_user_id'],
            'full_name': c['full_name'],
            'headline': c['headline'],
            'profile_picture': c['profile_picture']
        } for c in connections]
    })
