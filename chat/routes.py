"""
Chat routes blueprint for messaging between connected users.
"""

from functools import wraps

from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from database.db import execute_query
from notifications.utils import create_notification


# Create the chat blueprint
chat_bp = Blueprint('chat', __name__, url_prefix='/chat')


def login_required(f):
    """Decorator to require user login for protected routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def get_connected_users(user_id):
    """
    Get all users that are connected (accepted) with the given user.
    Returns list of connected users with their info.
    """
    return execute_query(
        """
        SELECT 
            CASE 
                WHEN c.sender_id = %s THEN c.receiver_id
                ELSE c.sender_id
            END AS user_id,
            CASE 
                WHEN c.sender_id = %s THEN u2.full_name
                ELSE u1.full_name
            END AS full_name,
            CASE 
                WHEN c.sender_id = %s THEN u2.profile_pic
                ELSE u1.profile_pic
            END AS profile_pic
        FROM connections c
        INNER JOIN users u1 ON c.sender_id = u1.id
        INNER JOIN users u2 ON c.receiver_id = u2.id
        WHERE c.status = 'accepted' 
          AND (c.sender_id = %s OR c.receiver_id = %s)
        ORDER BY full_name ASC
        """,
        (user_id, user_id, user_id, user_id, user_id),
        fetch_all=True
    )


def is_connected(user_id, partner_id):
    """
    Check if two users are connected (accepted status).
    """
    connection = execute_query(
        """
        SELECT id FROM connections 
        WHERE status = 'accepted' 
          AND ((sender_id = %s AND receiver_id = %s) 
               OR (sender_id = %s AND receiver_id = %s))
        """,
        (user_id, partner_id, partner_id, user_id),
        fetch_one=True
    )
    return connection is not None


@chat_bp.route('/')
@login_required
def chat_list():
    """
    Display list of connected users to chat with.
    Also shows last message preview for each conversation.
    """
    user_id = session['user_id']
    
    # Get all connected users
    connected_users = get_connected_users(user_id) or []
    
    # Get last message for each conversation
    conversations = []
    for user in connected_users:
        partner_id = user['user_id']
        
        # Get the most recent message in this conversation
        last_message = execute_query(
            """
            SELECT message, created_at, sender_id 
            FROM messages 
            WHERE (sender_id = %s AND receiver_id = %s) 
               OR (sender_id = %s AND receiver_id = %s)
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (user_id, partner_id, partner_id, user_id),
            fetch_one=True
        )
        
        # Get unread count (messages from partner that are newer than last read)
        unread_count = execute_query(
            """
            SELECT COUNT(*) as count 
            FROM messages 
            WHERE sender_id = %s AND receiver_id = %s
            """,
            (partner_id, user_id),
            fetch_one=True
        )
        
        conversations.append({
            'user_id': partner_id,
            'full_name': user['full_name'],
            'profile_pic': user['profile_pic'],
            'last_message': last_message,
            'unread_count': unread_count['count'] if unread_count else 0
        })
    
    # Sort by last message time (most recent first)
    conversations.sort(
        key=lambda x: x['last_message']['created_at'] if x['last_message'] else '', 
        reverse=True
    )
    
    return render_template('chat/chat_list.html', conversations=conversations)


@chat_bp.route('/t/<int:partner_id>')
@login_required
def conversation(partner_id):
    """
    View message history with a specific user.
    """
    user_id = session['user_id']
    
    # Prevent chatting with yourself
    if partner_id == user_id:
        flash('You cannot chat with yourself.', 'warning')
        return redirect(url_for('chat.chat_list'))
    
    # Security check: ensure users are connected
    if not is_connected(user_id, partner_id):
        flash('You can only chat with your connections.', 'warning')
        return redirect(url_for('chat.chat_list'))
    
    # Get partner info
    partner = execute_query(
        "SELECT id, full_name, profile_pic FROM users WHERE id = %s",
        (partner_id,),
        fetch_one=True
    )
    
    if not partner:
        flash('User not found.', 'danger')
        return redirect(url_for('chat.chat_list'))
    
    # Fetch all messages between the two users (oldest first)
    messages = execute_query(
        """
        SELECT m.id, m.sender_id, m.receiver_id, m.message, m.created_at,
               u.full_name as sender_name, u.profile_pic as sender_pic
        FROM messages m
        INNER JOIN users u ON m.sender_id = u.id
        WHERE (m.sender_id = %s AND m.receiver_id = %s) 
           OR (m.sender_id = %s AND m.receiver_id = %s)
        ORDER BY m.created_at ASC
        """,
        (user_id, partner_id, partner_id, user_id),
        fetch_all=True
    )
    
    return render_template(
        'chat/conversation.html', 
        partner=partner, 
        messages=messages or [],
        current_user_id=user_id
    )


@chat_bp.route('/send/<int:partner_id>', methods=['POST'])
@login_required
def send_message(partner_id):
    """
    Send a message to a connected user.
    """
    user_id = session['user_id']
    
    # Prevent messaging yourself
    if partner_id == user_id:
        flash('You cannot message yourself.', 'warning')
        return redirect(url_for('chat.chat_list'))
    
    # Security check: ensure users are connected
    if not is_connected(user_id, partner_id):
        flash('You can only message your connections.', 'warning')
        return redirect(url_for('chat.chat_list'))
    
    # Get message content
    message = request.form.get('message', '').strip()
    
    if not message:
        flash('Message cannot be empty.', 'warning')
        return redirect(url_for('chat.conversation', partner_id=partner_id))
    
    # Insert message into database
    result = execute_query(
        """
        INSERT INTO messages (sender_id, receiver_id, message, created_at) 
        VALUES (%s, %s, %s, NOW())
        """,
        (user_id, partner_id, message),
        commit=True
    )
    
    if result is not None:
        # Notify the receiver about the new message
        try:
            sender_name = session.get('user_name', 'Someone')
            create_notification(
                user_id=partner_id,
                message=f"New message from {sender_name}",
                notification_type='message'
            )
        except Exception:
            pass  # Notification is optional
    else:
        flash('Failed to send message. Please try again.', 'danger')
    
    return redirect(url_for('chat.conversation', partner_id=partner_id))
