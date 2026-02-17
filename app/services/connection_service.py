"""
Connection service.
Handles sending, accepting, rejecting connection requests and checking connection status.
"""
from app.database.connection import execute_query, execute_insert, execute_update
from app.services import notification_service


def get_ordered_ids(user1, user2):
    """Return user IDs in consistent order (smaller first)."""
    return (min(user1, user2), max(user1, user2))


def send_request(from_user_id, to_user_id):
    """Send a connection request."""
    if from_user_id == to_user_id:
        return False, "Cannot connect with yourself"
    
    user_id_1, user_id_2 = get_ordered_ids(from_user_id, to_user_id)
    
    # Check if connection already exists
    existing = get_connection(user_id_1, user_id_2)
    if existing:
        if existing['status'] == 'pending':
            return False, "Request already pending"
        elif existing['status'] == 'accepted':
            return False, "Already connected"
        elif existing['status'] == 'rejected':
            # Allow re-requesting after rejection
            query = """
                UPDATE connections 
                SET status = 'pending', created_by = %s, requested_at = CURRENT_TIMESTAMP 
                WHERE connection_id = %s
            """
            execute_update(query, (from_user_id, existing['connection_id']))
            notification_service.notify_connection_request(to_user_id, from_user_id)
            return True, "Request sent"
    
    # Create new connection
    query = """
        INSERT INTO connections (user_id_1, user_id_2, status, created_by)
        VALUES (%s, %s, 'pending', %s)
    """
    conn_id = execute_insert(query, (user_id_1, user_id_2, from_user_id))
    
    if conn_id:
        notification_service.notify_connection_request(to_user_id, from_user_id)
        return True, conn_id
    return False, "Failed to send request"


def accept_request(connection_id, user_id):
    """Accept a pending connection request."""
    # Verify user is the recipient
    connection = get_connection_by_id(connection_id)
    if not connection:
        return False, "Request not found"
    
    if connection['status'] != 'pending':
        return False, "Request already processed"
    
    # User must be one of the parties but NOT the creator
    if user_id not in [connection['user_id_1'], connection['user_id_2']]:
        return False, "Not authorized"
    if connection['created_by'] == user_id:
        return False, "Cannot accept your own request"
    
    query = "UPDATE connections SET status = 'accepted', responded_at = CURRENT_TIMESTAMP WHERE connection_id = %s"
    execute_update(query, (connection_id,))
    
    # Notify the sender
    notification_service.notify_connection_accepted(connection['created_by'], user_id)
    
    
    # Log Activity
    try:
        from app.services import activity_service
        activity_service.log_activity(
            action_type='connection_made',
            user_id=user_id, # The person accepting
            item_type='user',
            item_id=connection['created_by'], # The person who requested
            details={'target_user': connection['created_by']}
        )
    except Exception as e:
        print(f"Error logging connection activity: {e}")

    return True, "Connection accepted"


def reject_request(connection_id, user_id):
    """Reject a pending connection request."""
    connection = get_connection_by_id(connection_id)
    if not connection:
        return False, "Request not found"
    
    if connection['status'] != 'pending':
        return False, "Request already processed"
    
    if user_id not in [connection['user_id_1'], connection['user_id_2']]:
        return False, "Not authorized"
    if connection['created_by'] == user_id:
        return False, "Cannot reject your own request"
    
    query = "UPDATE connections SET status = 'rejected', responded_at = CURRENT_TIMESTAMP WHERE connection_id = %s"
    execute_update(query, (connection_id,))
    
    return True, "Request rejected"


def get_connection(user_id_1, user_id_2):
    """Get connection between two users."""
    id1, id2 = get_ordered_ids(user_id_1, user_id_2)
    query = "SELECT * FROM connections WHERE user_id_1 = %s AND user_id_2 = %s"
    return execute_query(query, (id1, id2), fetch_one=True)


def get_connection_by_id(connection_id):
    """Get connection by ID."""
    query = "SELECT * FROM connections WHERE connection_id = %s"
    return execute_query(query, (connection_id,), fetch_one=True)


def get_connection_status(user1, user2):
    """Get connection status between two users."""
    connection = get_connection(user1, user2)
    if not connection:
        return 'none'
    return connection['status']


def are_connected(user1, user2):
    """Check if two users are connected."""
    return get_connection_status(user1, user2) == 'accepted'


def get_my_connections(user_id):
    """Get list of connected users."""
    query = """
        SELECT 
            c.connection_id,
            c.requested_at,
            CASE 
                WHEN c.user_id_1 = %s THEN c.user_id_2 
                ELSE c.user_id_1 
            END as connected_user_id,
            p.full_name, p.headline, p.profile_picture
        FROM connections c
        LEFT JOIN profiles p ON p.user_id = CASE 
            WHEN c.user_id_1 = %s THEN c.user_id_2 
            ELSE c.user_id_1 
        END
        WHERE (c.user_id_1 = %s OR c.user_id_2 = %s) AND c.status = 'accepted'
        ORDER BY c.responded_at DESC
    """
    return execute_query(query, (user_id, user_id, user_id, user_id), fetch_all=True) or []


def get_pending_requests(user_id):
    """Get pending requests received by user."""
    query = """
        SELECT 
            c.connection_id,
            c.created_by,
            c.requested_at,
            p.user_id, p.full_name, p.headline, p.profile_picture
        FROM connections c
        JOIN profiles p ON p.user_id = c.created_by
        WHERE (c.user_id_1 = %s OR c.user_id_2 = %s) 
          AND c.status = 'pending'
          AND c.created_by != %s
        ORDER BY c.requested_at DESC
    """
    return execute_query(query, (user_id, user_id, user_id), fetch_all=True) or []


def get_sent_requests(user_id):
    """Get pending requests sent by user."""
    query = """
        SELECT 
            c.connection_id,
            c.requested_at,
            CASE 
                WHEN c.user_id_1 = %s THEN c.user_id_2 
                ELSE c.user_id_1 
            END as to_user_id,
            p.full_name, p.headline, p.profile_picture
        FROM connections c
        LEFT JOIN profiles p ON p.user_id = CASE 
            WHEN c.user_id_1 = %s THEN c.user_id_2 
            ELSE c.user_id_1 
        END
        WHERE (c.user_id_1 = %s OR c.user_id_2 = %s) 
          AND c.status = 'pending'
          AND c.created_by = %s
        ORDER BY c.requested_at DESC
    """
    return execute_query(query, (user_id, user_id, user_id, user_id, user_id), fetch_all=True) or []


