"""
Connections routes blueprint for managing user connections.
"""

from functools import wraps

from flask import Blueprint, render_template, redirect, url_for, flash, session, request, abort
from database.db import execute_query
from notifications.utils import create_notification


# Create the connections blueprint
connections_bp = Blueprint('connections', __name__, url_prefix='/connections')


def login_required(f):
    """Decorator to require user login for protected routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@connections_bp.route('/send/<int:user_id>', methods=['POST'])
@login_required
def send_request(user_id):
    """
    Send a connection request to another user.
    """
    sender_id = session['user_id']
    
    # Prevent self-connection
    if sender_id == user_id:
        flash('You cannot connect with yourself.', 'warning')
        return redirect(url_for('profile.view_profile', user_id=user_id))
    
    # Check if connection already exists (in either direction)
    existing = execute_query(
        """
        SELECT id, status FROM connections 
        WHERE (sender_id = %s AND receiver_id = %s) 
           OR (sender_id = %s AND receiver_id = %s)
        """,
        (sender_id, user_id, user_id, sender_id),
        fetch_one=True
    )
    
    if existing:
        if existing['status'] == 'pending':
            flash('A connection request is already pending.', 'info')
        elif existing['status'] == 'accepted':
            flash('You are already connected with this user.', 'info')
        return redirect(url_for('profile.view_profile', user_id=user_id))
    
    # Insert new connection request
    result = execute_query(
        """
        INSERT INTO connections (sender_id, receiver_id, status, created_at) 
        VALUES (%s, %s, 'pending', NOW())
        """,
        (sender_id, user_id),
        commit=True
    )
    
    if result is not None:
        flash('Connection request sent successfully!', 'success')
        # Send notification to receiver
        try:
            sender_name = session.get('user_name', 'Someone')
            create_notification(
                user_id=user_id,
                message=f"You have a new connection request from {sender_name}",
                notification_type='connection'
            )
        except Exception:
            pass  # Notification is optional, don't fail the request
    else:
        flash('Failed to send connection request. Please try again.', 'danger')
    
    return redirect(url_for('profile.view_profile', user_id=user_id))


@connections_bp.route('/requests')
@login_required
def incoming_requests():
    """
    View all pending incoming connection requests.
    """
    user_id = session['user_id']
    
    # Fetch pending requests where current user is the receiver
    requests = execute_query(
        """
        SELECT c.id, c.sender_id, c.created_at, 
               u.full_name, u.profile_pic, u.bio
        FROM connections c
        INNER JOIN users u ON c.sender_id = u.id
        WHERE c.receiver_id = %s AND c.status = 'pending'
        ORDER BY c.created_at DESC
        """,
        (user_id,),
        fetch_all=True
    )
    
    # Also get count of sent pending requests
    sent_count = execute_query(
        "SELECT COUNT(*) as count FROM connections WHERE sender_id = %s AND status = 'pending'",
        (user_id,),
        fetch_one=True
    )
    
    return render_template(
        'connections/requests.html', 
        requests=requests or [],
        sent_pending_count=sent_count['count'] if sent_count else 0
    )


@connections_bp.route('/respond/<int:connection_id>/<action>', methods=['POST'])
@login_required
def respond_request(connection_id, action):
    """
    Accept or reject a connection request.
    """
    user_id = session['user_id']
    
    # Validate action
    if action not in ['accept', 'reject']:
        flash('Invalid action.', 'danger')
        return redirect(url_for('connections.incoming_requests'))
    
    # Fetch the connection request
    connection = execute_query(
        "SELECT * FROM connections WHERE id = %s",
        (connection_id,),
        fetch_one=True
    )
    
    if not connection:
        flash('Connection request not found.', 'danger')
        return redirect(url_for('connections.incoming_requests'))
    
    # Security check: ensure current user is the receiver
    if connection['receiver_id'] != user_id:
        flash('You are not authorized to respond to this request.', 'danger')
        return redirect(url_for('connections.incoming_requests'))
    
    # Check if still pending
    if connection['status'] != 'pending':
        flash('This request has already been processed.', 'info')
        return redirect(url_for('connections.incoming_requests'))
    
    if action == 'accept':
        # Update status to accepted
        execute_query(
            "UPDATE connections SET status = 'accepted' WHERE id = %s",
            (connection_id,),
            commit=True
        )
        flash('Connection request accepted!', 'success')
        
        # Notify the sender that their request was accepted
        try:
            sender_id = connection['sender_id']
            receiver_name = session.get('user_name', 'Someone')
            create_notification(
                user_id=sender_id,
                message=f"{receiver_name} accepted your connection request",
                notification_type='connection'
            )
        except Exception:
            pass  # Notification is optional
    else:
        # Delete the request to allow re-requesting later
        execute_query(
            "DELETE FROM connections WHERE id = %s",
            (connection_id,),
            commit=True
        )
        flash('Connection request declined.', 'info')
    
    return redirect(url_for('connections.incoming_requests'))


@connections_bp.route('/list')
@login_required
def my_connections():
    """
    View all accepted connections.
    """
    user_id = session['user_id']
    
    # Fetch all accepted connections where current user is sender or receiver
    # Use CASE to determine the "other" user
    connections = execute_query(
        """
        SELECT 
            c.id AS connection_id,
            c.created_at,
            CASE 
                WHEN c.sender_id = %s THEN c.receiver_id
                ELSE c.sender_id
            END AS other_user_id,
            CASE 
                WHEN c.sender_id = %s THEN u2.full_name
                ELSE u1.full_name
            END AS other_user_name,
            CASE 
                WHEN c.sender_id = %s THEN u2.profile_pic
                ELSE u1.profile_pic
            END AS other_user_pic,
            CASE 
                WHEN c.sender_id = %s THEN u2.bio
                ELSE u1.bio
            END AS other_user_bio
        FROM connections c
        INNER JOIN users u1 ON c.sender_id = u1.id
        INNER JOIN users u2 ON c.receiver_id = u2.id
        WHERE c.status = 'accepted' 
          AND (c.sender_id = %s OR c.receiver_id = %s)
        ORDER BY c.created_at DESC
        """,
        (user_id, user_id, user_id, user_id, user_id, user_id),
        fetch_all=True
    )
    
    return render_template('connections/my_connections.html', connections=connections or [])


@connections_bp.route('/remove/<int:connection_id>', methods=['POST'])
@login_required
def remove_connection(connection_id):
    """
    Remove an existing connection.
    """
    user_id = session['user_id']
    
    # Fetch the connection
    connection = execute_query(
        "SELECT * FROM connections WHERE id = %s",
        (connection_id,),
        fetch_one=True
    )
    
    if not connection:
        flash('Connection not found.', 'danger')
        return redirect(url_for('connections.my_connections'))
    
    # Security check: ensure current user is either sender or receiver
    if connection['sender_id'] != user_id and connection['receiver_id'] != user_id:
        flash('You are not authorized to remove this connection.', 'danger')
        return redirect(url_for('connections.my_connections'))
    
    # Delete the connection
    execute_query(
        "DELETE FROM connections WHERE id = %s",
        (connection_id,),
        commit=True
    )
    
    flash('Connection removed.', 'info')
    return redirect(url_for('connections.my_connections'))


@connections_bp.route('/cancel/<int:connection_id>', methods=['POST'])
@login_required
def cancel_request(connection_id):
    """
    Cancel a sent connection request that is still pending.
    """
    user_id = session['user_id']
    
    # Fetch the connection
    connection = execute_query(
        "SELECT * FROM connections WHERE id = %s AND status = 'pending'",
        (connection_id,),
        fetch_one=True
    )
    
    if not connection:
        flash('Pending request not found.', 'danger')
        return redirect(url_for('connections.incoming_requests'))
    
    # Security check: ensure current user is the sender
    if connection['sender_id'] != user_id:
        flash('You are not authorized to cancel this request.', 'danger')
        return redirect(url_for('connections.incoming_requests'))
    
    # Delete the request
    execute_query(
        "DELETE FROM connections WHERE id = %s",
        (connection_id,),
        commit=True
    )
    
    flash('Connection request cancelled.', 'info')
    
    referrer = request.referrer
    if referrer:
        return redirect(referrer)
    return redirect(url_for('connections.incoming_requests'))


def get_connection_status(user_id, other_user_id):
    """
    Helper function to get connection status between two users.
    Returns: None, 'pending_sent', 'pending_received', 'accepted'
    """
    if not user_id or user_id == other_user_id:
        return None
    
    connection = execute_query(
        """
        SELECT id, sender_id, receiver_id, status 
        FROM connections 
        WHERE (sender_id = %s AND receiver_id = %s) 
           OR (sender_id = %s AND receiver_id = %s)
        """,
        (user_id, other_user_id, other_user_id, user_id),
        fetch_one=True
    )
    
    if not connection:
        return None
    
    if connection['status'] == 'accepted':
        return 'accepted'
    elif connection['status'] == 'pending':
        if connection['sender_id'] == user_id:
            return 'pending_sent'
        else:
            return 'pending_received'
    
    return None
