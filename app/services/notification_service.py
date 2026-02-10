from app.models.notification import Notification

class NotificationService:
    @staticmethod
    def create_notification(user_id, type, content, related_id=None):
        return Notification.create(user_id, type, content, related_id)

    @staticmethod
    def get_user_notifications(user_id):
        return Notification.get_all(user_id)

    @staticmethod
    def get_unread_count(user_id):
        return Notification.get_unread_count(user_id)
        
    @staticmethod
    def mark_read(notification_id, user_id):
        return Notification.mark_as_read(notification_id, user_id)
        
    @staticmethod
    def mark_all_read(user_id):
        return Notification.mark_all_read(user_id)
