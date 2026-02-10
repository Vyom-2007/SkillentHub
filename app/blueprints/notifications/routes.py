from flask import Blueprint, jsonify, session, render_template, redirect, url_for
from app.services.notification_service import NotificationService

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')

@notifications_bp.route('/')
def index():
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    
    notifications = NotificationService.get_user_notifications(session['user_id'])
    # Mark all as read when visiting page (optional, or via button)
    return render_template('notifications/index.html', notifications=notifications)

@notifications_bp.route('/api/unread-count')
def unread_count():
    if 'user_id' not in session: return jsonify({'count': 0})
    count = NotificationService.get_unread_count(session['user_id'])
    return jsonify({'count': count})

@notifications_bp.route('/api/mark-all-read', methods=['POST'])
def mark_all_read():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    NotificationService.mark_all_read(session['user_id'])
    return jsonify({'success': True})
