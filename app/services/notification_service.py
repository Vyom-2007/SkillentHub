"""
Notification service.
Centralized class for creating, fetching, and managing notifications.
"""
import json
from app.database.connection import execute_query, execute_insert, execute_update


class NotificationService:
    """Centralized notification service."""

    # ========== CORE CRUD ==========

    def create_notification(self, user_id, notification_type, content, related_id=None, payload=None):
        """Create a new notification with optional JSON payload."""
        payload_str = json.dumps(payload) if payload else None
        query = """
            INSERT INTO notifications (user_id, type, content, payload, related_id)
            VALUES (%s, %s, %s, %s, %s)
        """
        return execute_insert(query, (user_id, notification_type, content, payload_str, related_id))

    def get_unread_count(self, user_id):
        """Get count of unread notifications (lightweight query)."""
        query = "SELECT COUNT(*) as count FROM notifications WHERE user_id = %s AND is_read = 0"
        result = execute_query(query, (user_id,), fetch_one=True)
        return result['count'] if result else 0

    def get_notifications(self, user_id, limit=50, offset=0, filter_type=None, unread_only=False):
        """Get notifications for a user with optional filters."""
        params = [user_id]

        query = """
            SELECT notification_id, type, content, payload, related_id, is_read, created_at
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

    def get_recent_notifications(self, user_id, limit=5):
        """Get recent notifications for dropdown preview."""
        query = """
            SELECT notification_id, type, content, payload, related_id, is_read, created_at
            FROM notifications
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """
        return execute_query(query, (user_id, limit), fetch_all=True) or []

    def mark_as_read(self, notification_id, user_id):
        """Mark a single notification as read."""
        query = "UPDATE notifications SET is_read = 1 WHERE notification_id = %s AND user_id = %s"
        return execute_update(query, (notification_id, user_id))

    def mark_all_as_read(self, user_id):
        """Mark all notifications as read for a user."""
        query = "UPDATE notifications SET is_read = 1 WHERE user_id = %s AND is_read = 0"
        return execute_update(query, (user_id,))

    def delete_notification(self, notification_id, user_id):
        """Delete a notification."""
        query = "DELETE FROM notifications WHERE notification_id = %s AND user_id = %s"
        return execute_update(query, (notification_id, user_id))

    # ========== ICON HELPER ==========

    def get_notification_icon(self, notification_type):
        """Get Bootstrap icon class for notification type."""
        icons = {
            'post_like': 'bi-heart-fill text-danger',
            'post_comment': 'bi-chat-fill text-primary',
            'new_message': 'bi-envelope-fill text-info',
            'application_update': 'bi-briefcase-fill text-success',
            'application_submitted': 'bi-send-fill text-primary',
            'interview_invite': 'bi-camera-video-fill text-warning',
            'interview_update': 'bi-calendar-check text-info',
            'event_reminder': 'bi-calendar-event text-warning',
            'connection_request': 'bi-person-plus-fill text-purple',
            'connection_accepted': 'bi-person-check-fill text-success',
            'team_invitation': 'bi-people-fill text-info',
            'team_invitation_accepted': 'bi-people-fill text-success',
        }
        return icons.get(notification_type, 'bi-bell-fill text-secondary')

    # ========== TYPED TRIGGER METHODS ==========

    def notify_application_submitted(self, user_id, item_title, item_type, application_id):
        """Notify candidate that their application was submitted."""
        try:
            content = f"Your application for '{item_title}' ({item_type}) has been submitted successfully."
            payload = {'item_title': item_title, 'item_type': item_type, 'application_id': application_id}
            self.create_notification(user_id, 'application_submitted', content, related_id=application_id, payload=payload)
            return True
        except Exception as e:
            print(f"Error sending application submitted notification: {e}")
            return False

    def notify_application_update(self, user_id, item_title, status, application_id):
        """Notify user of application status update."""
        try:
            content = f"Your application for '{item_title}' is now {status.capitalize()}."
            payload = {'item_title': item_title, 'status': status, 'application_id': application_id}
            self.create_notification(user_id, 'application_update', content, related_id=application_id, payload=payload)
            return True
        except Exception as e:
            print(f"Error sending application update notification: {e}")
            return False

    def notify_interview_invite(self, recruiter_id, candidate_id, interview_id, scheduled_at_str):
        """Notify candidate of a new interview."""
        try:
            recruiter = execute_query("SELECT company_name FROM recruiters WHERE recruiter_id=%s", (recruiter_id,), fetch_one=True)
            company_name = recruiter['company_name'] if recruiter else "A recruiter"
            content = f"{company_name} has scheduled an interview with you on {scheduled_at_str}. Please confirm."
            payload = {'company_name': company_name, 'scheduled_at': str(scheduled_at_str), 'interview_id': interview_id}
            self.create_notification(candidate_id, 'interview_invite', content, related_id=interview_id, payload=payload)
            return True
        except Exception as e:
            print(f"Error sending interview invite notification: {e}")
            return False

    def notify_interview_update(self, recruiter_id, candidate_id, interview_id, status):
        """Notify candidate of interview status update."""
        try:
            content = f"Interview status updated to {status}."
            payload = {'status': status, 'interview_id': interview_id}
            self.create_notification(candidate_id, 'interview_update', content, related_id=interview_id, payload=payload)
            return True
        except Exception as e:
            print(f"Error sending interview update notification: {e}")
            return False

    def notify_interview_reschedule(self, recruiter_id, candidate_id, interview_id, new_time_str):
        """Notify candidate of interview reschedule."""
        try:
            content = f"Interview rescheduled to {new_time_str}. Please confirm."
            payload = {'new_time': str(new_time_str), 'interview_id': interview_id}
            self.create_notification(candidate_id, 'interview_update', content, related_id=interview_id, payload=payload)
            return True
        except Exception as e:
            print(f"Error sending interview reschedule notification: {e}")
            return False

    def notify_new_message(self, sender_id, receiver_id, sender_type):
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
            payload = {'sender_id': sender_id, 'sender_type': sender_type, 'sender_name': sender_name}
            self.create_notification(receiver_id, 'new_message', content, related_id=sender_id, payload=payload)
            return True
        except Exception as e:
            print(f"Error sending message notification: {e}")
            return False

    def notify_connection_request(self, sender_id, receiver_id):
        """Notify user of a connection request."""
        try:
            sender = execute_query("SELECT full_name FROM profiles WHERE user_id = %s", (sender_id,), fetch_one=True)
            sender_name = sender['full_name'] if sender else 'Someone'
            content = f"{sender_name} sent you a connection request"
            self.create_notification(receiver_id, 'connection_request', content, related_id=sender_id)
            return True
        except Exception as e:
            print(f"Error sending connection request notification: {e}")
            return False

    def notify_connection_accepted(self, accepter_id, receiver_id):
        """Notify user that their request was accepted."""
        try:
            accepter = execute_query("SELECT full_name FROM profiles WHERE user_id = %s", (accepter_id,), fetch_one=True)
            name = accepter['full_name'] if accepter else 'Someone'
            content = f"{name} accepted your connection request"
            self.create_notification(receiver_id, 'connection_accepted', content, related_id=accepter_id)
            return True
        except Exception as e:
            print(f"Error sending connection accepted notification: {e}")
            return False

    def notify_team_invitation(self, invited_user_id, inviter_id, team_name, team_id):
        """Notify user of team invitation."""
        try:
            inviter = execute_query("SELECT full_name FROM profiles WHERE user_id = %s", (inviter_id,), fetch_one=True)
            inviter_name = inviter['full_name'] if inviter else 'Someone'
            content = f"{inviter_name} invited you to join team '{team_name}'"
            self.create_notification(invited_user_id, 'team_invitation', content, related_id=team_id)
            return True
        except Exception as e:
            print(f"Error sending team invitation notification: {e}")
            return False

    def notify_team_joined(self, leader_id, joiner_id, team_name, team_id):
        """Notify team leader that someone joined."""
        try:
            joiner = execute_query("SELECT full_name FROM profiles WHERE user_id = %s", (joiner_id,), fetch_one=True)
            joiner_name = joiner['full_name'] if joiner else 'Someone'
            content = f"{joiner_name} joined your team '{team_name}'"
            self.create_notification(leader_id, 'team_invitation_accepted', content, related_id=team_id)
            return True
        except Exception as e:
            print(f"Error sending team joined notification: {e}")
            return False


# Module-level singleton instance for backward compatibility
notification_service = NotificationService()

# Expose top-level functions that delegate to the singleton
# This preserves backward compatibility with existing callers
create_notification = notification_service.create_notification
get_unread_count = notification_service.get_unread_count
get_notifications = notification_service.get_notifications
get_recent_notifications = notification_service.get_recent_notifications
mark_as_read = notification_service.mark_as_read
mark_all_as_read = notification_service.mark_all_as_read
delete_notification = notification_service.delete_notification
get_notification_icon = notification_service.get_notification_icon
notify_connection_request = notification_service.notify_connection_request
notify_connection_accepted = notification_service.notify_connection_accepted
notify_interview_invite = notification_service.notify_interview_invite
notify_interview_update = notification_service.notify_interview_update
notify_interview_reschedule = notification_service.notify_interview_reschedule
notify_new_message = notification_service.notify_new_message
notify_team_invitation = notification_service.notify_team_invitation
notify_team_joined = notification_service.notify_team_joined
notify_application_update = notification_service.notify_application_update
notify_application_submitted = notification_service.notify_application_submitted
