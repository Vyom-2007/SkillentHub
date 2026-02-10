from database.connection import get_db_connection

class Message:
    @staticmethod
    def send(sender_id, receiver_id, content):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO messages (sender_id, receiver_id, content) 
                    VALUES (%s, %s, %s)
                """
                cursor.execute(sql, (sender_id, receiver_id, content))
            conn.commit()
            return True
        finally:
            conn.close()

    @staticmethod
    def get_conversations(user_id):
        # Initial prototyping: complex query to get last message for each unique partner
        # For simplicity in prototype:
        # 1. Get all unique partners
        # 2. For each, get last message
        # Valid SQL:
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                 sql = """
                    SELECT 
                        CASE WHEN m.sender_id = %s THEN m.receiver_id ELSE m.sender_id END as other_user_id,
                        MAX(m.created_at) as last_msg_time
                    FROM messages m
                    WHERE m.sender_id = %s OR m.receiver_id = %s
                    GROUP BY other_user_id
                    ORDER BY last_msg_time DESC
                 """
                 cursor.execute(sql, (user_id, user_id, user_id))
                 conversations = cursor.fetchall()
                 
                 # Populate details
                 results = []
                 for conv in conversations:
                     other_id = conv['other_user_id']
                     
                     # Get user info
                     cursor.execute("SELECT full_name FROM users WHERE user_id=%s", (other_id,))
                     user_info = cursor.fetchone()
                     
                     # Get profile pic
                     cursor.execute("SELECT profile_picture FROM profiles WHERE user_id=%s", (other_id,))
                     profile_info = cursor.fetchone()
                     
                     # Get last message text
                     cursor.execute("""
                        SELECT content, is_read, sender_id FROM messages 
                        WHERE (sender_id=%s AND receiver_id=%s) OR (sender_id=%s AND receiver_id=%s)
                        ORDER BY created_at DESC LIMIT 1
                     """, (user_id, other_id, other_id, user_id))
                     last_msg = cursor.fetchone()
                     
                     results.append({
                         'user_id': other_id,
                         'full_name': user_info['full_name'],
                         'profile_picture': profile_info['profile_picture'] if profile_info else None,
                         'last_message': last_msg['content'],
                         'last_time': conv['last_msg_time'],
                         'unread': not last_msg['is_read'] and last_msg['sender_id'] != user_id
                     })
                 return results
        finally:
            conn.close()

    @staticmethod
    def get_conversation_messages(user1, user2):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                    SELECT * FROM messages 
                    WHERE (sender_id = %s AND receiver_id = %s) 
                       OR (sender_id = %s AND receiver_id = %s)
                    ORDER BY created_at ASC
                """
                cursor.execute(sql, (user1, user2, user2, user1))
                messages = cursor.fetchall()
                
                # Mark as read
                update_sql = "UPDATE messages SET is_read = 1 WHERE sender_id = %s AND receiver_id = %s"
                cursor.execute(update_sql, (user2, user1)) # Mark received messages as read
                conn.commit()
                
                return messages
        finally:
            conn.close()
