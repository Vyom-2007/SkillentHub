from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from app.models.message import Message
from app.models.user import User

messages_bp = Blueprint('messages', __name__, url_prefix='/messages')

@messages_bp.route('/')
def index():
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    
    conversations = Message.get_conversations(session['user_id'])
    return render_template('messages/index.html', conversations=conversations)

@messages_bp.route('/<int:user_id>')
def chat(user_id):
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    
    conversations = Message.get_conversations(session['user_id'])
    messages = Message.get_conversation_messages(session['user_id'], user_id)
    target_user = User.get_by_id(user_id)
    
    return render_template('messages/index.html', 
                           conversations=conversations, 
                           messages=messages, 
                           active_user=target_user)

@messages_bp.route('/api/send', methods=['POST'])
def send_message():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    receiver_id = data.get('receiver_id')
    content = data.get('content')
    
    if Message.send(session['user_id'], receiver_id, content):
        return jsonify({'success': True})
    return jsonify({'error': 'Failed'}), 500

@messages_bp.route('/api/<int:user_id>/new')
def get_new_messages(user_id):
    # Polling endpoint - Simplified: returning all for now or logic to filter by ID
    # For robust polling, we need 'since' timestamp or ID
    # Implementing full sync later.
    return jsonify({'messages': []})
