"""
Messages routes blueprint.
Handles direct messaging between users.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from functools import wraps
from app.services import message_service

messages_bp = Blueprint('messages', __name__)



def get_current_user():
    """Get current user ID and type from session."""
    if session.get('user_id'):
        return session.get('user_id'), 'user'
    elif session.get('recruiter_id'):
        return session.get('recruiter_id'), 'recruiter'
    return None, None


def login_required(f):
    """Decorator to require login (user or recruiter)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id, _ = get_current_user()
        if not user_id:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def api_login_required(f):
    """Decorator for API endpoints (user or recruiter)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id, _ = get_current_user()
        if not user_id:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function


@messages_bp.route('/messages')
@login_required
def messages():
    """Display messages page with conversation list and optional chat."""
    current_id, current_type = get_current_user()
    target_id = request.args.get('user', type=int)
    target_type = request.args.get('type', 'user') # Default to user
    
    # Get conversations list
    conversations = message_service.get_conversations(current_id, current_type)
    
    # If target user specified, get chat history
    chat_history = []
    target_user = None
    last_message_id = 0
    
    if target_id:
        target_info = message_service.get_user_info(target_id, target_type)
        if target_info:
            chat_history = message_service.get_chat_history(current_id, current_type, target_id, target_type)
            # Mark messages as read
            message_service.mark_as_read(current_id, current_type, target_id, target_type)
            if chat_history:
                last_message_id = chat_history[-1]['message_id']
            target_user = target_info
    
    from datetime import date, timedelta
    today = date.today()
    yesterday = today - timedelta(days=1)

    return render_template('messages/messages.html',
                           conversations=conversations,
                           chat_history=chat_history,
                           target_user=target_user,
                           last_message_id=last_message_id,
                           today=today,
                           yesterday=yesterday,
                           current_user_type=current_type)


@messages_bp.route('/api/messages/send', methods=['POST'])
@api_login_required
def send_message():
    """Send a message to a user/recruiter."""
    current_id, current_type = get_current_user()
    
    if request.is_json:
        data = request.json
        receiver_id = data.get('receiver_id')
        receiver_type = data.get('receiver_type', 'user')
        content = data.get('content', '')
    else:
        receiver_id = request.form.get('receiver_id', type=int)
        receiver_type = request.form.get('receiver_type', 'user')
        content = request.form.get('content', '')
    
    if not receiver_id:
        return jsonify({'error': 'Receiver ID required'}), 400
    
    message, error = message_service.send_message(current_id, receiver_id, content, sender_type=current_type, receiver_type=receiver_type)
    
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


@messages_bp.route('/api/messages/<int:other_id>/new')
@api_login_required
def get_new_messages(other_id):
    """Get new messages from a user/recruiter (polling endpoint)."""
    current_id, current_type = get_current_user()
    other_type = request.args.get('type', 'user')
    since_id = request.args.get('since', 0, type=int)
    
    messages = message_service.get_new_messages(current_id, other_id, since_id, current_type=current_type, other_type=other_type)
    
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


@messages_bp.route('/api/messages/<int:other_id>/read', methods=['POST'])
@api_login_required
def mark_as_read(other_id):
    """Mark messages from a user/recruiter as read."""
    current_id, current_type = get_current_user()
    other_type = request.args.get('type', 'user')
    success = message_service.mark_as_read(current_id, current_type, other_id, other_type)
    return jsonify({'success': success})


@messages_bp.route('/api/messages/unread')
@api_login_required
def get_unread_counts():
    """Get unread message counts for sidebar updates."""
    current_id, current_type = get_current_user()
    total = message_service.get_total_unread_count(current_id, current_type)
    
    return jsonify({
        'success': True,
        'total': total
    })


@messages_bp.route('/api/conversations')
@api_login_required
def get_conversations_api():
    """Get updated conversations list for sidebar."""
    current_id, current_type = get_current_user()
    conversations = message_service.get_conversations(current_id, current_type)
    
    return jsonify({
        'success': True,
        'conversations': [{
            'other_id': c['other_id'],
            'other_type': c['other_type'],
            'name': c['name'],
            'picture': c['picture'],
            'headline': c['headline'],
            'last_message': c['last_message'],
            'last_message_time': c['last_msg_time'].isoformat() if c['last_msg_time'] else None,
            'unread_count': c['unread_count']
        } for c in conversations]
    })
