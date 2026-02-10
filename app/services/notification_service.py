"""
Notification service.
Handles creating, fetching, and managing notifications.
"""
from app.database.connection import execute_query, execute_insert, execute_update


def create_notification(user_id, notification_type, content, related_id=None):
    """Create a new notification."""
    query = """
        INSERT INTO notifications (user_id, type, content, related_id)
        VALUES (%s, %s, %s, %s)
    """
    return execute_insert(query, (user_id, notification_type, content, related_id))


def get_unread_count(user_id):
    """Get count of unread notifications (lightweight query)."""
    query = "SELECT COUNT(*) as count FROM notifications WHERE user_id = %s AND is_read = 0"
    result = execute_query(query, (user_id,), fetch_one=True)
    return result['count'] if result else 0


def get_notifications(user_id, limit=50, offset=0, filter_type=None, unread_only=False):
    """Get notifications for a user with optional filters."""
    params = [user_id]
    
    query = """
        SELECT notification_id, type, content, related_id, is_read, created_at
        FROM notifications
        WHERE user_id = %s
    """
    
    if filter_type:
        query += " AND type = %s"
        params.append(filter_type)
    
    if unread_only:
        query += " AND is_read = 0"
    
    query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    
    return execute_query(query, tuple(params), fetch_all=True) or []


def get_recent_notifications(user_id, limit=5):
    """Get recent notifications for dropdown preview."""
    query = """
        SELECT notification_id, type, content, related_id, is_read, created_at
        FROM notifications
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT %s
    """
    return execute_query(query, (user_id, limit), fetch_all=True) or []


def mark_as_read(notification_id, user_id):
    """Mark a single notification as read."""
    query = "UPDATE notifications SET is_read = 1 WHERE notification_id = %s AND user_id = %s"
    return execute_update(query, (notification_id, user_id))


def mark_all_as_read(user_id):
    """Mark all notifications as read for a user."""
    query = "UPDATE notifications SET is_read = 1 WHERE user_id = %s AND is_read = 0"
    return execute_update(query, (user_id,))


def delete_notification(notification_id, user_id):
    """Delete a notification."""
    query = "DELETE FROM notifications WHERE notification_id = %s AND user_id = %s"
    return execute_update(query, (notification_id, user_id))


def get_notification_icon(notification_type):
    """Get Bootstrap icon class for notification type."""
    icons = {
        'post_like': 'bi-heart-fill text-danger',
        'post_comment': 'bi-chat-fill text-primary',
        'new_message': 'bi-envelope-fill text-info',
        'application_update': 'bi-briefcase-fill text-success',
        'event_reminder': 'bi-calendar-event text-warning',
        'connection': 'bi-person-plus-fill text-purple'
    }
    return icons.get(notification_type, 'bi-bell-fill text-secondary')
