"""
Messages routes blueprint.
Handles direct messaging between users.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from functools import wraps
from app.services import message_service

messages_bp = Blueprint('messages', __name__)


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


@messages_bp.route('/messages')
@login_required
def messages():
    """Display messages page with conversation list and optional chat."""
    user_id = session.get('user_id')
    target_user_id = request.args.get('user', type=int)
    
    # Get conversations list
    conversations = message_service.get_conversations(user_id)
    
    # If target user specified, get chat history
    chat_history = []
    target_user = None
    last_message_id = 0
    
    if target_user_id:
        target_user = message_service.get_user_info(target_user_id)
        if target_user:
            chat_history = message_service.get_chat_history(user_id, target_user_id)
            # Mark messages as read
            message_service.mark_as_read(user_id, target_user_id)
            if chat_history:
                last_message_id = chat_history[-1]['message_id']
    
    return render_template('messages/messages.html',
                           conversations=conversations,
                           chat_history=chat_history,
                           target_user=target_user,
                           last_message_id=last_message_id)


@messages_bp.route('/api/messages/send', methods=['POST'])
@api_login_required
def send_message():
    """Send a message to a user."""
    user_id = session.get('user_id')
    
    if request.is_json:
        data = request.json
        receiver_id = data.get('receiver_id')
        content = data.get('content', '')
    else:
        receiver_id = request.form.get('receiver_id', type=int)
        content = request.form.get('content', '')
    
    if not receiver_id:
        return jsonify({'error': 'Receiver ID required'}), 400
    
    message, error = message_service.send_message(user_id, receiver_id, content)
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({
        'success': True,
        'message': {
            'message_id': message['message_id'],
            'sender_id': message['sender_id'],
            'receiver_id': message['receiver_id'],
            'content': message['content'],
            'created_at': message['created_at'].isoformat() if message['created_at'] else None
        }
    })


@messages_bp.route('/api/messages/<int:user_id>/new')
@api_login_required
def get_new_messages(user_id):
    """Get new messages from a user (polling endpoint)."""
    current_user_id = session.get('user_id')
    since_id = request.args.get('since', 0, type=int)
    
    messages = message_service.get_new_messages(current_user_id, user_id, since_id)
    
    return jsonify({
        'success': True,
        'messages': [{
            'message_id': m['message_id'],
            'sender_id': m['sender_id'],
            'receiver_id': m['receiver_id'],
            'content': m['content'],
            'created_at': m['created_at'].isoformat() if m['created_at'] else None,
            'sender_name': m['sender_name'],
            'sender_picture': m['sender_picture']
        } for m in messages]
    })


@messages_bp.route('/api/messages/<int:user_id>/read', methods=['POST'])
@api_login_required
def mark_as_read(user_id):
    """Mark messages from a user as read."""
    current_user_id = session.get('user_id')
    success = message_service.mark_as_read(current_user_id, user_id)
    return jsonify({'success': success})


@messages_bp.route('/api/messages/unread')
@api_login_required
def get_unread_counts():
    """Get unread message counts for sidebar updates."""
    user_id = session.get('user_id')
    total = message_service.get_total_unread_count(user_id)
    by_sender = message_service.get_unread_counts_by_sender(user_id)
    
    return jsonify({
        'success': True,
        'total': total,
        'by_sender': by_sender
    })


@messages_bp.route('/api/conversations')
@api_login_required
def get_conversations():
    """Get updated conversations list for sidebar."""
    user_id = session.get('user_id')
    conversations = message_service.get_conversations(user_id)
    
    return jsonify({
        'success': True,
        'conversations': [{
            'user_id': c['user_id'],
            'full_name': c['full_name'],
            'profile_picture': c['profile_picture'],
            'headline': c['headline'],
            'last_message': c['last_message'],
            'last_message_time': c['last_message_time'].isoformat() if c['last_message_time'] else None,
            'unread_count': c['unread_count']
        } for c in conversations]
    })
