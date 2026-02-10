from database.connection import get_db_connection

class Notification:
    @staticmethod
    def create(user_id, type, content, related_id=None):
        conn = get_db_connection()
        if not conn: return False
        try:
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO notifications (user_id, type, content, related_id)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(sql, (user_id, type, content, related_id))
            conn.commit()
            return True
        finally:
            conn.close()

    @staticmethod
    def get_all(user_id, limit=20, offset=0):
        conn = get_db_connection()
        if not conn: return []
        try:
            with conn.cursor() as cursor:
                sql = """
                    SELECT * FROM notifications 
                    WHERE user_id = %s 
                    ORDER BY created_at DESC 
                    LIMIT %s OFFSET %s
                """
                cursor.execute(sql, (user_id, limit, offset))
                return cursor.fetchall()
        finally:
            conn.close()

    @staticmethod
    def get_unread_count(user_id):
        conn = get_db_connection()
        if not conn: return 0
        try:
            with conn.cursor() as cursor:
                sql = "SELECT COUNT(*) as count FROM notifications WHERE user_id = %s AND is_read = 0"
                cursor.execute(sql, (user_id,))
                result = cursor.fetchone()
                return result['count']
        finally:
            conn.close()

    @staticmethod
    def mark_as_read(notification_id, user_id):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                sql = "UPDATE notifications SET is_read = 1 WHERE notification_id = %s AND user_id = %s"
                cursor.execute(sql, (notification_id, user_id))
            conn.commit()
            return True
        finally:
            conn.close()

    @staticmethod
    def mark_all_read(user_id):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                sql = "UPDATE notifications SET is_read = 1 WHERE user_id = %s"
                cursor.execute(sql, (user_id,))
            conn.commit()
            return True
        finally:
            conn.close()
