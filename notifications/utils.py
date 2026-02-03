"""
Notification utility functions.

This module provides helper functions for creating notifications
that can be imported by other modules.
"""

from database.db import execute_query


def create_notification(user_id, message, notification_type='general'):
    """
    Create a new notification for a user.
    
    This function can be called from any module to create notifications.
    
    Args:
        user_id (int): The ID of the user to notify.
        message (str): The notification message.
        notification_type (str): Type of notification. Common types:
            - 'general': General notifications
            - 'connection': Connection-related (request, accepted)
            - 'message': New message notification
            - 'like': Post liked notification
            - 'comment': Comment notification
            - 'opportunity': Job/opportunity notification
            - 'event': Event notification
    
    Returns:
        int or None: The ID of the created notification, or None if failed.
    
    Example:
        from notifications.utils import create_notification
        create_notification(user_id=5, message="John sent you a connection request", notification_type='connection')
    """
    result = execute_query(
        """
        INSERT INTO notifications (user_id, message, type, is_read, created_at) 
        VALUES (%s, %s, %s, FALSE, NOW())
        """,
        (user_id, message, notification_type),
        commit=True
    )
    return result


def create_bulk_notifications(user_ids, message, notification_type='general'):
    """
    Create notifications for multiple users.
    
    Args:
        user_ids (list): List of user IDs to notify.
        message (str): The notification message.
        notification_type (str): Type of notification.
    
    Returns:
        int: Number of notifications created.
    """
    count = 0
    for user_id in user_ids:
        result = create_notification(user_id, message, notification_type)
        if result is not None:
            count += 1
    return count


def get_unread_count(user_id):
    """
    Get the count of unread notifications for a user.
    
    Args:
        user_id (int): The user ID.
    
    Returns:
        int: Number of unread notifications.
    """
    result = execute_query(
        "SELECT COUNT(*) as count FROM notifications WHERE user_id = %s AND is_read = FALSE",
        (user_id,),
        fetch_one=True
    )
    return result['count'] if result else 0


def mark_all_as_read(user_id):
    """
    Mark all notifications as read for a user.
    
    Args:
        user_id (int): The user ID.
    
    Returns:
        bool: True if successful.
    """
    execute_query(
        "UPDATE notifications SET is_read = TRUE WHERE user_id = %s AND is_read = FALSE",
        (user_id,),
        commit=True
    )
    return True
