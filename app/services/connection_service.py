from app.database.connection import get_db_connection


def get_connection_status(user_id_1, user_id_2):
    """
    Check the connection status between two users.
    Returns: 'accepted', 'pending', or None.
    """
    if user_id_1 == user_id_2:
        return 'self'

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT status, created_by FROM connections "
                "WHERE (user_id_1 = %s AND user_id_2 = %s) "
                "   OR (user_id_1 = %s AND user_id_2 = %s) "
                "ORDER BY requested_at DESC LIMIT 1",
                (user_id_1, user_id_2, user_id_2, user_id_1),
            )
            row = cur.fetchone()
            if not row:
                return None
            return row['status']
    finally:
        conn.close()


def search_users(query, current_user_id, offset=0):
    """
    Search users by name/headline. 
    Returns list of dicts with calculated connection status relative to current_user.
    Status can be: 'connected', 'pending_sent', 'pending_received', 'none', 'self'
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            sql = """
                SELECT 
                    u.user_id, u.full_name, 
                    p.headline, p.profile_picture,
                    c.status as db_status, c.created_by
                FROM users u
                JOIN profiles p ON u.user_id = p.user_id
                LEFT JOIN connections c ON 
                    (c.user_id_1 = u.user_id AND c.user_id_2 = %s) OR 
                    (c.user_id_1 = %s AND c.user_id_2 = u.user_id)
                WHERE u.full_name LIKE %s OR p.headline LIKE %s
                LIMIT 10 OFFSET %s
            """
            search_pattern = f"%{query}%"
            cur.execute(sql, (current_user_id, current_user_id, search_pattern, search_pattern, offset))
            rows = cur.fetchall()
            
            results = []
            for row in rows:
                if row['user_id'] == current_user_id:
                    status = 'self'
                elif row['db_status'] == 'accepted':
                    status = 'connected'
                elif row['db_status'] == 'pending':
                    if row['created_by'] == current_user_id:
                        status = 'pending_sent'
                    else:
                        status = 'pending_received'
                else:
                    status = 'none'  # covers None (no row) and 'rejected' (treat as none so they can try again?)
                    # If rejected, maybe show rejected? Spec didn't say. Let's stick to 'none' or maybe 'rejected' if needed.
                    # Usually 'rejected' means they can't connect again for a while, but for simplicity let's treat as 'none' 
                    # allowing retry, or 'rejected' state.
                    if row['db_status'] == 'rejected':
                         status = 'none' 

                results.append({
                    'user_id': row['user_id'],
                    'full_name': row['full_name'],
                    'headline': row['headline'],
                    'profile_picture': row['profile_picture'],
                    'connection_status': status
                })
            return results
    finally:
        conn.close()


def get_my_connections(user_id):
    """Get list of accepted connections."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            sql = """
                SELECT 
                    u.user_id, u.full_name, 
                    p.headline, p.profile_picture
                FROM connections c
                JOIN users u ON (u.user_id = c.user_id_1 OR u.user_id = c.user_id_2)
                JOIN profiles p ON u.user_id = p.user_id
                WHERE (c.user_id_1 = %s OR c.user_id_2 = %s)
                  AND c.status = 'accepted'
                  AND u.user_id != %s
            """
            cur.execute(sql, (user_id, user_id, user_id))
            return cur.fetchall()
    finally:
        conn.close()


def get_pending_requests(user_id, sent_by_me=False):
    """Get pending connection requests (either sent or received)."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            if sent_by_me:
                # I sent these requests, waiting for others to accept
                sql = """
                    SELECT 
                        c.connection_id, c.requested_at,
                        u.user_id, u.full_name, 
                        p.headline, p.profile_picture
                    FROM connections c
                    JOIN users u ON (u.user_id = c.user_id_1 OR u.user_id = c.user_id_2)
                    JOIN profiles p ON u.user_id = p.user_id
                    WHERE c.created_by = %s 
                      AND c.status = 'pending'
                      AND u.user_id != %s
                """
                cur.execute(sql, (user_id, user_id))
            else:
                # Others sent these to me, waiting for me to accept
                # Example: I am ID 2. Row is (1, 2) created by 1.
                # I want to see User 1.
                sql = """
                    SELECT 
                        c.connection_id, c.requested_at,
                        u.user_id, u.full_name, 
                        p.headline, p.profile_picture
                    FROM connections c
                    JOIN users u ON (u.user_id = c.user_id_1 OR u.user_id = c.user_id_2)
                    JOIN profiles p ON u.user_id = p.user_id
                    WHERE (c.user_id_1 = %s OR c.user_id_2 = %s)
                      AND c.status = 'pending'
                      AND c.created_by != %s
                      AND u.user_id != %s
                """
                cur.execute(sql, (user_id, user_id, user_id, user_id))
            return cur.fetchall()
    finally:
        conn.close()


def send_request(from_id, to_id):
    """Send a connection request."""
    if from_id == to_id: return False, "Cannot connect to yourself"

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Check existing
            cur.execute(
                "SELECT status FROM connections WHERE "
                "(user_id_1=%s AND user_id_2=%s) OR (user_id_1=%s AND user_id_2=%s)",
                (from_id, to_id, to_id, from_id)
            )
            existing = cur.fetchone()
            if existing:
                if existing['status'] == 'pending':
                    return False, "Request already pending"
                if existing['status'] == 'accepted':
                    return False, "Already connected"
                # If rejected, maybe allow re-send? Let's allow update or re-insert?
                # For simplicity, delete old rejected row and insert new?
                # Or just update status to pending.
                # Let's try to update, if fail insert.
                cur.execute(
                    "UPDATE connections SET status='pending', created_by=%s, requested_at=NOW() "
                    "WHERE (user_id_1=%s AND user_id_2=%s) OR (user_id_1=%s AND user_id_2=%s)",
                    (from_id, from_id, to_id, to_id, from_id)
                )
            else:
                # Insert
                # Sort IDs to maintain consistency if we want, but schema has unique constraint on (id1, id2).
                # To be safe against (2,1) vs (1,2) duplicate errors if unique index is bidirectional (it's not usually, but let's see schema).
                # Schema: UNIQUE KEY `unique_connection` (`user_id_1`,`user_id_2`)
                # This only enforces (1,2) is unique. (2,1) is NOT blocked by this index unless we sort.
                # Logic: Let's always insert sorted IDs to prevent (1,2) and (2,1) existing simultaneously.
                u1, u2 = sorted([from_id, to_id])
                cur.execute(
                    "INSERT INTO connections (user_id_1, user_id_2, status, created_by) "
                    "VALUES (%s, %s, 'pending', %s)",
                    (u1, u2, from_id)
                )

            # Notification
            cur.execute(
                "INSERT INTO notifications (user_id, type, content, related_id) "
                "VALUES (%s, 'connection_request', 'Someone sent you a connection request', %s)",
                (to_id, from_id) 
            )
            conn.commit()
            return True, "Request sent"
    finally:
        conn.close()


def accept_request(connection_id, user_id):
    """Accept a connection request."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # verify it exists and is pending and I am the recipient
            cur.execute(
                "SELECT * FROM connections WHERE connection_id=%s AND status='pending'",
                (connection_id,)
            )
            row = cur.fetchone()
            if not row:
                return False, "Request not found"
            
            # Recipient check: created_by should NOT be me.
            # And I must be one of the users.
            if row['created_by'] == user_id:
                return False, "Cannot accept your own request"
            
            if user_id not in (row['user_id_1'], row['user_id_2']):
                return False, "Not authorized"

            cur.execute(
                "UPDATE connections SET status='accepted', responded_at=NOW() "
                "WHERE connection_id=%s",
                (connection_id,)
            )

            # Notify sender
            sender_id = row['created_by']
            cur.execute(
                "INSERT INTO notifications (user_id, type, content, related_id) "
                "VALUES (%s, 'connection_accepted', 'Your connection request was accepted', %s)",
                (sender_id, user_id)
            )
            conn.commit()
            return True, "Connected"
    finally:
        conn.close()


def reject_request(connection_id, user_id):
    """Reject a connection request."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM connections WHERE connection_id=%s AND status='pending'",
                (connection_id,)
            )
            row = cur.fetchone()
            if not row: return False, "Request not found"
            
            if row['created_by'] == user_id: return False, "Cannot reject own request"
            if user_id not in (row['user_id_1'], row['user_id_2']): return False, "Not authorized"

            cur.execute(
                "UPDATE connections SET status='rejected', responded_at=NOW() "
                "WHERE connection_id=%s",
                (connection_id,)
            )
            conn.commit()
            return True, "Rejected"
    finally:
        conn.close()


def cancel_request(connection_id, user_id):
    """Cancel a sent request."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM connections WHERE connection_id=%s AND status='pending'",
                (connection_id,)
            )
            row = cur.fetchone()
            if not row: return False, "Request not found"

            # Must be created by me
            if row['created_by'] != user_id: return False, "Not your request"

            cur.execute("DELETE FROM connections WHERE connection_id=%s", (connection_id,))
            conn.commit()
            return True, "Cancelled"
    finally:
        conn.close()
