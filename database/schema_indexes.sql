-- Index for efficient unread notification counting
CREATE INDEX idx_notifications_user_read ON notifications(user_id, is_read);
