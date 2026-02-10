
from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from app.services import message_service

recruiter_messages_bp = Blueprint('recruiter_messages', __name__)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('recruiter_id'):
            return redirect(url_for('auth_recruiter.login'))
        return f(*args, **kwargs)
    return decorated_function

@recruiter_messages_bp.route('/recruiter/messages')
@login_required
def messages():
    """Recruiter Inbox."""
    recruiter_id = session.get('recruiter_id')
    
    # Defaults
    target_id = request.args.get('user', type=int)
    target_type = request.args.get('type', 'user') # Recruiters message users generally
    
    conversations = message_service.get_conversations(recruiter_id, 'recruiter')
    
    chat_history = []
    target_user = None
    
    if target_id:
        target_info = message_service.get_user_info(target_id, target_type)
        if target_info:
            chat_history = message_service.get_chat_history(recruiter_id, 'recruiter', target_id, target_type)
            message_service.mark_as_read(recruiter_id, 'recruiter', target_id, target_type)
            target_user = target_info
            
    return render_template('recruiter/messages.html',
                           conversations=conversations,
                           chat_history=chat_history,
                           target_user=target_user)
