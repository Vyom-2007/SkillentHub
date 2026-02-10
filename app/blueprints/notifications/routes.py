"""
Notifications routes.
Handles notification API endpoints and full page.
"""
from flask import Blueprint, render_template, request, session, jsonify
from functools import wraps
from app.services import notification_service

notifications_bp = Blueprint('notifications', __name__)


def login_required(f):
    """Decorator to require login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function


# ========== API ENDPOINTS ==========

@notifications_bp.route('/api/notifications/unread-count')
@login_required
def unread_count():
    """Get unread notification count (lightweight for polling)."""
    user_id = session.get('user_id')
    count = notification_service.get_unread_count(user_id)
    return jsonify({'count': count})


@notifications_bp.route('/api/notifications/recent')
@login_required
def recent_notifications():
    """Get recent notifications for dropdown preview."""
    user_id = session.get('user_id')
    notifications = notification_service.get_recent_notifications(user_id, limit=5)
    
    # Format for JSON response
    result = []
    for n in notifications:
        result.append({
            'id': n['notification_id'],
            'type': n['type'],
            'content': n['content'],
            'is_read': bool(n['is_read']),
            'icon': notification_service.get_notification_icon(n['type']),
            'time_ago': format_time_ago(n['created_at']),
            'related_id': n['related_id']
        })
    
    return jsonify({'notifications': result})


@notifications_bp.route('/api/notifications/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_read(notification_id):
    """Mark a single notification as read."""
    user_id = session.get('user_id')
    notification_service.mark_as_read(notification_id, user_id)
    return jsonify({'success': True})


@notifications_bp.route('/api/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    """Mark all notifications as read."""
    user_id = session.get('user_id')
    notification_service.mark_all_as_read(user_id)
    return jsonify({'success': True})


# ========== PAGE ROUTES ==========

@notifications_bp.route('/notifications')
def notifications_page():
    """Display full notifications page."""
    if not session.get('user_id'):
        from flask import redirect, url_for, flash
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('auth.login'))
    
    user_id = session.get('user_id')
    page = request.args.get('page', 1, type=int)
    filter_type = request.args.get('type', '').strip()
    unread_only = request.args.get('unread', '').lower() == 'true'
    
    per_page = 50
    offset = (page - 1) * per_page
    
    notifications = notification_service.get_notifications(
        user_id,
        limit=per_page,
        offset=offset,
        filter_type=filter_type if filter_type else None,
        unread_only=unread_only
    )
    
    # Add icons to notifications
    for n in notifications:
        n['icon'] = notification_service.get_notification_icon(n['type'])
    
    unread_count = notification_service.get_unread_count(user_id)
    
    return render_template('notifications/list.html',
                           notifications=notifications,
                           unread_count=unread_count,
                           current_type=filter_type,
                           unread_only=unread_only,
                           page=page)


# ========== HELPERS ==========

def format_time_ago(dt):
    """Format datetime as relative time string."""
    if not dt:
        return ''
    
    from datetime import datetime
    now = datetime.now()
    diff = now - dt
    
    seconds = diff.total_seconds()
    if seconds < 60:
        return 'Just now'
    elif seconds < 3600:
        mins = int(seconds / 60)
        return f'{mins}m ago'
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f'{hours}h ago'
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f'{days}d ago'
    else:
        return dt.strftime('%b %d')
