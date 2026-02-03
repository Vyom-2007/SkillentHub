"""
Notifications module initialization.

This module handles user notifications - creating, viewing, and managing them.
"""

from notifications.routes import notifications_bp
from notifications.utils import create_notification, get_unread_count, mark_all_as_read

__all__ = ['notifications_bp', 'create_notification', 'get_unread_count', 'mark_all_as_read']
