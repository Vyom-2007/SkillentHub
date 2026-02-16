"""
Message service.
Handles direct messaging between users and recruiters.
"""
from app.database.connection import execute_query, execute_insert, execute_update, get_db_connection


def get_conversations(entity_id, entity_type='user'):
    """
    Get list of conversations for a user/recruiter with latest message and unread count.
    Normalized to return:
        - other_id
        - other_type
        - name
        - picture
        - headline
        - last_message
        - last_message_time
        - unread_count
    """
    # This query is complex because we need to handle:
    # 1. Messages where I am sender (to User OR Recruiter)
    # 2. Messages where I am receiver (from User OR Recruiter)
    # AND we need to join with appropriate profile table based on type.
    
    # Strategy: Get list of distinct (other_id, other_type) from messages
    # Then join with users/recruiters manually or via UNION.
    
    query = """
        SELECT 
            CASE 
                WHEN sender_id = %s AND sender_type = %s THEN receiver_id 
                ELSE sender_id 
            END as other_id,
            CASE 
                WHEN sender_id = %s AND sender_type = %s THEN receiver_type
                ELSE sender_type 
            END as other_type,
            MAX(created_at) as last_msg_time,
            (
                SELECT content FROM messages m2 
                WHERE (m2.sender_id = other_id AND m2.sender_type = other_type AND m2.receiver_id = %s AND m2.receiver_type = %s)
                   OR (m2.sender_id = %s AND m2.sender_type = %s AND m2.receiver_id = other_id AND m2.receiver_type = other_type)
                ORDER BY created_at DESC LIMIT 1
            ) as last_message,
            (
                SELECT COUNT(*) FROM messages m3
                WHERE m3.sender_id = other_id AND m3.sender_type = other_type 
                  AND m3.receiver_id = %s AND m3.receiver_type = %s 
                  AND m3.is_read = 0
            ) as unread_count
        FROM messages
        WHERE (sender_id = %s AND sender_type = %s) OR (receiver_id = %s AND receiver_type = %s)
        GROUP BY other_id, other_type
        ORDER BY last_msg_time DESC
    """
    
    params = (
        entity_id, entity_type, # Case 1
        entity_id, entity_type, # Case 2
        entity_id, entity_type, # Subquery 1 (receiver me)
        entity_id, entity_type, # Subquery 1 (sender me)
        entity_id, entity_type, # Subquery 2 (unread)
        entity_id, entity_type, # Where clause 1
        entity_id, entity_type  # Where clause 2
    )
    
    convs = execute_query(query, params, fetch_all=True) or []
    
    # Enrich with profile info
    results = []
    for c in convs:
        other_id = c['other_id']
        other_type = c['other_type']
        
        info = {}
        if other_type == 'user':
            u = execute_query("""
                SELECT p.full_name as name, p.profile_picture as picture, p.headline 
                FROM profiles p WHERE p.user_id = %s
            """, (other_id,), fetch_one=True)
            if u: info = u
        elif other_type == 'recruiter':
            r = execute_query("""
                SELECT company_name as name, 'default_company.png' as picture, 'Recruiter' as headline 
                FROM recruiters WHERE recruiter_id = %s
            """, (other_id,), fetch_one=True)
            if r: info = r
            
        if info:
            c.update(info)
            # Ensure picture has a value
            if not c.get('picture'):
                c['picture'] = 'default.png'
            results.append(c)
            
    return results


def get_chat_history(entity1_id, entity1_type, entity2_id, entity2_type):
    """Get all messages between two entities."""
    query = """
        SELECT 
            m.*,
            CASE 
                WHEN m.sender_type = 'user' THEN (SELECT full_name FROM profiles WHERE user_id = m.sender_id)
                WHEN m.sender_type = 'recruiter' THEN (SELECT company_name FROM recruiters WHERE recruiter_id = m.sender_id)
            END as sender_name,
             CASE 
                WHEN m.sender_type = 'user' THEN (SELECT profile_picture FROM profiles WHERE user_id = m.sender_id)
                WHEN m.sender_type = 'recruiter' THEN 'default_company.png'
            END as sender_picture
        FROM messages m
        WHERE 
           (m.sender_id = %s AND m.sender_type = %s AND m.receiver_id = %s AND m.receiver_type = %s)
           OR 
           (m.sender_id = %s AND m.sender_type = %s AND m.receiver_id = %s AND m.receiver_type = %s)
        ORDER BY m.created_at ASC
    """
    params = (
        entity1_id, entity1_type, entity2_id, entity2_type,
        entity2_id, entity2_type, entity1_id, entity1_type
    )
    return execute_query(query, params, fetch_all=True) or []


def send_message(sender_id, receiver_id, content, sender_type='user', receiver_type='user'):
    """Send a message."""
    if not content or not content.strip():
        return None, "Message cannot be empty"
    
    # Check permission
    # If sender is recruiter, allow strict messaging (no connection needed)
    if sender_type == 'user' and receiver_type == 'user':
         if not can_message_user(sender_id, receiver_id):
             return None, "You must be connected to send messages to this user"
    
    # For Recruiter -> User, allow.
    # For User -> Recruiter? Usually allowed if Recruiter messaged first? 
    # Or if applying? For now, if conversation exists, allow.
    if sender_type == 'user' and receiver_type == 'recruiter':
        # Check if conversation exists
         history = get_chat_history(sender_id, sender_type, receiver_id, receiver_type)
         if not history:
             # Maybe allow if applied? Complex check. 
             # Let's Allow for now to simplify "Reply" flow.
             pass

    content = content.strip()[:1000]
    
    query = """
        INSERT INTO messages (sender_id, sender_type, receiver_id, receiver_type, content) 
        VALUES (%s, %s, %s, %s, %s)
    """
    message_id = execute_insert(query, (sender_id, sender_type, receiver_id, receiver_type, content))
    
    if message_id:
        # Send in-app notification if receiver is a user
        if receiver_type == 'user':
            try:
                from app.services import notification_service
                # Get sender name
                sender_name = "Someone"
                if sender_type == 'recruiter':
                    r = execute_query("SELECT company_name FROM recruiters WHERE recruiter_id=%s", (sender_id,), fetch_one=True)
                    if r: sender_name = r['company_name']
                else:
                    u = execute_query("SELECT full_name FROM profiles WHERE user_id=%s", (sender_id,), fetch_one=True)
                    if u: sender_name = u['full_name']

                notification_service.create_notification(
                    user_id=receiver_id,
                    notification_type='new_message',
                    content=f"New message from {sender_name}",
                    related_id=sender_id
                )
            except Exception as e:
                print(f"Error sending message notification: {e}")

        return get_message_by_id(message_id), None
    return None, "Failed to send message"


def can_message_user(user1, user2):
    """Check if two USERS can message each other."""
    # Check for existing conversation
    history_query = """
        SELECT 1 FROM messages 
        WHERE (sender_id = %s AND sender_type='user' AND receiver_id = %s AND receiver_type='user') 
           OR (sender_id = %s AND sender_type='user' AND receiver_id = %s AND receiver_type='user')
        LIMIT 1
    """
    has_history = execute_query(history_query, (user1, user2, user2, user1), fetch_one=True)
    if has_history:
        return True
    
    from app.services import connection_service
    return connection_service.are_connected(user1, user2)


def get_message_by_id(message_id):
    """Get a single message by ID."""
    query = "SELECT * FROM messages WHERE message_id = %s"
    msg = execute_query(query, (message_id,), fetch_one=True)
    if msg:
        # Resolve sender name/pic
        if msg['sender_type'] == 'user':
            u = execute_query("SELECT full_name as sender_name, profile_picture as sender_picture FROM profiles WHERE user_id=%s", (msg['sender_id'],), fetch_one=True)
            if u: msg.update(u)
        elif msg['sender_type'] == 'recruiter':
             r = execute_query("SELECT company_name as sender_name, 'default_company.png' as sender_picture FROM recruiters WHERE recruiter_id=%s", (msg['sender_id'],), fetch_one=True)
             if r: msg.update(r)
    return msg


def get_unread_counts_by_sender(entity_id, entity_type='user'):
    """Get unread counts grouped by sender."""
    query = """
        SELECT sender_id, sender_type, COUNT(*) as count 
        FROM messages 
        WHERE receiver_id = %s AND receiver_type = %s AND is_read = 0 
        GROUP BY sender_id, sender_type
    """
    results = execute_query(query, (entity_id, entity_type), fetch_all=True) or []
    # Return dict somewhat like { 'user_1': 5, 'recruiter_2': 1 } or just list?
    # Original returned {sender_id: count}. 
    # Let's return list of objects or dict keyed by composite key?
    # For backward compatibility, if caller expects dict {id: count}, it might break if IDs collide across types.
    # But for now, let's return a list or dict with type.
    # Actually, the sidebar JS likely expects a map. 
    # Let's return {f"{type}_{id}": count}
    return {f"{r['sender_type']}_{r['sender_id']}": r['count'] for r in results}


def get_new_messages(entity1_id, entity2_id, since_id=0, current_type='user', other_type='user'):
    """
    Get new messages between two entities since a specific message ID.
    Fetch both sent and received messages to keep multiple tabs in sync.
    """
    # 1. Fetch new messages
    # Logic: Get messages where:
    # (Sender is Me AND Receiver is Them) OR (Sender is Them AND Receiver is Me)
    query = """
        SELECT 
            m.*,
            CASE 
                WHEN m.sender_type = 'user' THEN (SELECT full_name FROM profiles WHERE user_id = m.sender_id)
                WHEN m.sender_type = 'recruiter' THEN (SELECT company_name FROM recruiters WHERE recruiter_id = m.sender_id)
            END as sender_name,
             CASE 
                WHEN m.sender_type = 'user' THEN (SELECT profile_picture FROM profiles WHERE user_id = m.sender_id)
                WHEN m.sender_type = 'recruiter' THEN 'default_company.png'
            END as sender_picture
        FROM messages m
        WHERE (
            (m.sender_id = %s AND m.sender_type = %s AND m.receiver_id = %s AND m.receiver_type = %s) OR 
            (m.sender_id = %s AND m.sender_type = %s AND m.receiver_id = %s AND m.receiver_type = %s)
        )
        AND m.message_id > %s
        ORDER BY m.created_at ASC
    """
    params = (
        entity1_id, current_type, entity2_id, other_type,
        entity2_id, other_type, entity1_id, current_type,
        since_id
    )
    
    messages = execute_query(query, params, fetch_all=True) or []
    
    # 2. Mark incoming messages as read
    # Use the helper function for consistency
    mark_as_read(entity1_id, current_type, entity2_id, other_type)
            
    return messages


def mark_as_read(entity_id, entity_type, other_id, other_type):
    """Mark all messages from other entity as read."""
    # Logic: Update where Receiver is Me AND Sender is Them
    query = """
        UPDATE messages 
        SET is_read = 1 
        WHERE receiver_id = %s AND receiver_type = %s 
          AND sender_id = %s AND sender_type = %s 
          AND is_read = 0
    """
    execute_update(query, (entity_id, entity_type, other_id, other_type))
    return True


def get_total_unread_count(entity_id, entity_type='user'):
    """Get total unread message count."""
    query = "SELECT COUNT(*) as count FROM messages WHERE receiver_id = %s AND receiver_type = %s AND is_read = 0"
    result = execute_query(query, (entity_id, entity_type), fetch_one=True)
    return result['count'] if result else 0


def get_user_info(entity_id, entity_type='user'):
    """Get generic info for chat header."""
    if entity_type == 'user':
        return execute_query("""
            SELECT user_id as id, 'user' as type, full_name as name, profile_picture as picture, headline 
            FROM profiles WHERE user_id = %s
        """, (entity_id,), fetch_one=True)
    elif entity_type == 'recruiter':
        return execute_query("""
            SELECT recruiter_id as id, 'recruiter' as type, company_name as name, 'default_company.png' as picture, 'Recruiter' as headline 
            FROM recruiters WHERE recruiter_id = %s
        """, (entity_id,), fetch_one=True)
    return None

