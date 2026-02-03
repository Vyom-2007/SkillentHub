"""
Notifications routes blueprint for viewing and managing notifications.
"""

from functools import wraps

from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from database.db import execute_query
from notifications.utils import get_unread_count, mark_all_as_read


# Create the notifications blueprint
notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')


def login_required(f):
    """Decorator to require user login for protected routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@notifications_bp.route('/')
@login_required
def list_notifications():
    """
    Display all notifications for the current user.
    Ordered by created_at DESC (newest first).
    """
    user_id = session['user_id']
    
    # Fetch all notifications for the user
    notifications = execute_query(
        """
        SELECT id, message, type, is_read, created_at 
        FROM notifications 
        WHERE user_id = %s 
        ORDER BY created_at DESC
        """,
        (user_id,),
        fetch_all=True
    )
    
    # Get counts
    total_count = len(notifications) if notifications else 0
    unread_count = sum(1 for n in notifications if not n['is_read']) if notifications else 0
    
    return render_template(
        'notifications/list.html', 
        notifications=notifications or [],
        total_count=total_count,
        unread_count=unread_count
    )


@notifications_bp.route('/read/<int:notification_id>', methods=['POST'])
@login_required
def mark_as_read(notification_id):
    """
    Mark a specific notification as read.
    """
    user_id = session['user_id']
    
    # Update notification (only if owned by current user)
    execute_query(
        "UPDATE notifications SET is_read = TRUE WHERE id = %s AND user_id = %s",
        (notification_id, user_id),
        commit=True
    )
    
    # Redirect back
    referrer = request.referrer
    if referrer:
        return redirect(referrer)
    return redirect(url_for('notifications.list_notifications'))


@notifications_bp.route('/read-all', methods=['POST'])
@login_required
def mark_all_read():
    """
    Mark all notifications as read.
    """
    user_id = session['user_id']
    mark_all_as_read(user_id)
    flash('All notifications marked as read.', 'success')
    return redirect(url_for('notifications.list_notifications'))


@notifications_bp.route('/delete/<int:notification_id>', methods=['POST'])
@login_required
def delete_notification(notification_id):
    """
    Delete a specific notification.
    """
    user_id = session['user_id']
    
    # Delete notification (only if owned by current user)
    execute_query(
        "DELETE FROM notifications WHERE id = %s AND user_id = %s",
        (notification_id, user_id),
        commit=True
    )
    
    flash('Notification deleted.', 'info')
    
    # Redirect back
    referrer = request.referrer
    if referrer:
        return redirect(referrer)
    return redirect(url_for('notifications.list_notifications'))


@notifications_bp.route('/clear-all', methods=['POST'])
@login_required
def clear_all():
    """
    Delete all notifications for the current user.
    """
    user_id = session['user_id']
    
    execute_query(
        "DELETE FROM notifications WHERE user_id = %s",
        (user_id,),
        commit=True
    )
    
    flash('All notifications cleared.', 'info')
    return redirect(url_for('notifications.list_notifications'))


# Context processor to inject unread count into all templates
@notifications_bp.app_context_processor
def inject_notification_count():
    """
    Inject unread notification count into all templates.
    This allows showing a badge on the notification icon in the navbar.
    """
    if 'user_id' in session:
        return {'unread_notification_count': get_unread_count(session['user_id'])}
    return {'unread_notification_count': 0}
