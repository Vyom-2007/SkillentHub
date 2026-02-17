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

# ========== TYPED HELPER METHODS ==========

def notify_connection_request(sender_id, receiver_id):
    """Notify user of a connection request."""
    try:
        sender = execute_query("SELECT full_name FROM profiles WHERE user_id = %s", (sender_id,), fetch_one=True)
        sender_name = sender['full_name'] if sender else 'Someone'
        content = f"{sender_name} sent you a connection request"
        create_notification(receiver_id, 'connection_request', content, related_id=sender_id)
        return True
    except Exception as e:
        print(f"Error sending connection request notification: {e}")
        return False

def notify_connection_accepted(accepter_id, receiver_id):
    """Notify user that their request was accepted."""
    try:
        accepter = execute_query("SELECT full_name FROM profiles WHERE user_id = %s", (accepter_id,), fetch_one=True)
        name = accepter['full_name'] if accepter else 'Someone'
        content = f"{name} accepted your connection request"
        create_notification(receiver_id, 'connection_accepted', content, related_id=accepter_id)
        return True
    except Exception as e:
        print(f"Error sending connection accepted notification: {e}")
        return False

def notify_interview_invite(recruiter_id, candidate_id, interview_id, scheduled_at_str):
    """Notify candidate of a new interview."""
    try:
        recruiter = execute_query("SELECT company_name FROM recruiters WHERE recruiter_id=%s", (recruiter_id,), fetch_one=True)
        company_name = recruiter['company_name'] if recruiter else "A recruiter"
        content = f"{company_name} has scheduled an interview with you on {scheduled_at_str}. Please confirm."
        create_notification(candidate_id, 'interview_invite', content, related_id=interview_id)
        return True
    except Exception as e:
        print(f"Error sending interview invite notification: {e}")
        return False

def notify_interview_update(recruiter_id, candidate_id, interview_id, status):
    """Notify candidate of interview status update."""
    try:
        content = f"Interview status updated to {status}."
        create_notification(candidate_id, 'interview_update', content, related_id=interview_id)
        return True
    except Exception as e:
        print(f"Error sending interview update notification: {e}")
        return False

def notify_new_message(sender_id, receiver_id, sender_type):
    """Notify user of a new message."""
    try:
        sender_name = "Someone"
        if sender_type == 'recruiter':
            r = execute_query("SELECT company_name FROM recruiters WHERE recruiter_id=%s", (sender_id,), fetch_one=True)
            if r: sender_name = r['company_name']
        else:
            u = execute_query("SELECT full_name FROM profiles WHERE user_id=%s", (sender_id,), fetch_one=True)
            if u: sender_name = u['full_name']
            
        content = f"New message from {sender_name}"
        create_notification(receiver_id, 'new_message', content, related_id=sender_id)
        return True
    except Exception as e:
        print(f"Error sending message notification: {e}")
        return False

def notify_team_invitation(invited_user_id, inviter_id, team_name, team_id):
    """Notify user of team invitation."""
    try:
        inviter = execute_query("SELECT full_name FROM profiles WHERE user_id = %s", (inviter_id,), fetch_one=True)
        inviter_name = inviter['full_name'] if inviter else 'Someone'
        content = f"{inviter_name} invited you to join team '{team_name}'"
        create_notification(invited_user_id, 'team_invitation', content, related_id=team_id)
        return True
    except Exception as e:
        print(f"Error sending team invitation notification: {e}")
        return False

def notify_team_joined(leader_id, joiner_id, team_name, team_id):
    """Notify team leader that someone joined."""
    try:
        joiner = execute_query("SELECT full_name FROM profiles WHERE user_id = %s", (joiner_id,), fetch_one=True)
        joiner_name = joiner['full_name'] if joiner else 'Someone'
        content = f"{joiner_name} joined your team '{team_name}'"
        create_notification(leader_id, 'team_invitation_accepted', content, related_id=team_id)
        return True
    except Exception as e:
        print(f"Error sending team joined notification: {e}")
        return False

def notify_application_update(user_id, item_title, status, application_id):
    """Notify user of application status update."""
    try:
        content = f"Your application for {item_title} is now {status.capitalize()}."
        create_notification(user_id, 'application_update', content, related_id=application_id)
        return True
    except Exception as e:
        print(f"Error sending application update notification: {e}")
        return False
