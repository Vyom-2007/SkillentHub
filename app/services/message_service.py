"""
Message service.
Handles direct messaging between users.
"""
from app.database.connection import execute_query, execute_insert, get_db_connection


def get_conversations(user_id):
    """
    Get list of conversations for a user with latest message and unread count.
    Complex SQL: Get distinct users, latest message, and unread count per conversation.
    """
    query = """
        SELECT 
            u.user_id,
            p.full_name,
            p.profile_picture,
            p.headline,
            (
                SELECT content FROM messages 
                WHERE (sender_id = u.user_id AND receiver_id = %s) 
                   OR (sender_id = %s AND receiver_id = u.user_id)
                ORDER BY created_at DESC LIMIT 1
            ) as last_message,
            (
                SELECT created_at FROM messages 
                WHERE (sender_id = u.user_id AND receiver_id = %s) 
                   OR (sender_id = %s AND receiver_id = u.user_id)
                ORDER BY created_at DESC LIMIT 1
            ) as last_message_time,
            (
                SELECT COUNT(*) FROM messages 
                WHERE sender_id = u.user_id AND receiver_id = %s AND is_read = 0
            ) as unread_count
        FROM users u
        LEFT JOIN profiles p ON u.user_id = p.user_id
        WHERE u.user_id IN (
            SELECT DISTINCT 
                CASE 
                    WHEN sender_id = %s THEN receiver_id 
                    ELSE sender_id 
                END as other_user
            FROM messages 
            WHERE sender_id = %s OR receiver_id = %s
        )
        ORDER BY last_message_time DESC
    """
    params = (user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id)
    return execute_query(query, params, fetch_all=True) or []


def get_chat_history(current_user_id, other_user_id):
    """Get all messages between two users."""
    query = """
        SELECT 
            m.message_id,
            m.sender_id,
            m.receiver_id,
            m.content,
            m.is_read,
            m.created_at,
            p.full_name as sender_name,
            p.profile_picture as sender_picture
        FROM messages m
        LEFT JOIN profiles p ON m.sender_id = p.user_id
        WHERE (m.sender_id = %s AND m.receiver_id = %s)
           OR (m.sender_id = %s AND m.receiver_id = %s)
        ORDER BY m.created_at ASC
    """
    return execute_query(query, (current_user_id, other_user_id, other_user_id, current_user_id), fetch_all=True) or []


def send_message(sender_id, receiver_id, content):
    """Send a message to another user."""
    if not content or not content.strip():
        return None, "Message cannot be empty"
    
    # Check if users are connected OR have existing conversation
    if not can_message(sender_id, receiver_id):
        return None, "You must be connected to send messages to this user"
    
    content = content.strip()[:1000]  # Max 1000 chars
    
    query = "INSERT INTO messages (sender_id, receiver_id, content) VALUES (%s, %s, %s)"
    message_id = execute_insert(query, (sender_id, receiver_id, content))
    
    if message_id:
        # Return the created message
        return get_message_by_id(message_id), None
    return None, "Failed to send message"


def can_message(user1, user2):
    """
    Check if two users can message each other.
    Allowed if: connected OR have existing conversation history.
    """
    # Check for existing conversation (legacy support)
    history_query = """
        SELECT 1 FROM messages 
        WHERE (sender_id = %s AND receiver_id = %s) 
           OR (sender_id = %s AND receiver_id = %s)
        LIMIT 1
    """
    has_history = execute_query(history_query, (user1, user2, user2, user1), fetch_one=True)
    if has_history:
        return True
    
    # Check connection status
    from app.services import connection_service
    return connection_service.are_connected(user1, user2)


def get_message_by_id(message_id):
    """Get a single message by ID."""
    query = """
        SELECT 
            m.message_id,
            m.sender_id,
            m.receiver_id,
            m.content,
            m.is_read,
            m.created_at,
            p.full_name as sender_name,
            p.profile_picture as sender_picture
        FROM messages m
        LEFT JOIN profiles p ON m.sender_id = p.user_id
        WHERE m.message_id = %s
    """
    return execute_query(query, (message_id,), fetch_one=True)


def get_new_messages(current_user_id, other_user_id, since_id=0):
    """Get new messages from other user since a specific message ID."""
    query = """
        SELECT 
            m.message_id,
            m.sender_id,
            m.receiver_id,
            m.content,
            m.is_read,
            m.created_at,
            p.full_name as sender_name,
            p.profile_picture as sender_picture
        FROM messages m
        LEFT JOIN profiles p ON m.sender_id = p.user_id
        WHERE m.sender_id = %s AND m.receiver_id = %s AND m.message_id > %s
        ORDER BY m.created_at ASC
    """
    return execute_query(query, (other_user_id, current_user_id, since_id), fetch_all=True) or []


def mark_as_read(current_user_id, other_user_id):
    """Mark all messages from other user as read."""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            query = """
                UPDATE messages 
                SET is_read = 1 
                WHERE sender_id = %s AND receiver_id = %s AND is_read = 0
            """
            cursor.execute(query, (other_user_id, current_user_id))
        connection.commit()
        return True
    except Exception as e:
        print(f"Error marking messages as read: {e}")
        return False
    finally:
        connection.close()


def get_total_unread_count(user_id):
    """Get total unread message count for a user."""
    query = "SELECT COUNT(*) as count FROM messages WHERE receiver_id = %s AND is_read = 0"
    result = execute_query(query, (user_id,), fetch_one=True)
    return result['count'] if result else 0


def get_unread_counts_by_sender(user_id):
    """Get unread counts grouped by sender."""
    query = """
        SELECT sender_id, COUNT(*) as count 
        FROM messages 
        WHERE receiver_id = %s AND is_read = 0 
        GROUP BY sender_id
    """
    results = execute_query(query, (user_id,), fetch_all=True) or []
    return {r['sender_id']: r['count'] for r in results}


def get_user_info(user_id):
    """Get user info for chat header."""
    query = """
        SELECT u.user_id, p.full_name, p.profile_picture, p.headline
        FROM users u
        LEFT JOIN profiles p ON u.user_id = p.user_id
        WHERE u.user_id = %s
    """
    return execute_query(query, (user_id,), fetch_one=True)
