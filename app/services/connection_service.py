from app.database.connection import get_db_connection


def get_connection_status(user_id_1, user_id_2):
    """
    Check the connection status between two users.
    Returns: 'accepted', 'pending', or None.
    """
    if user_id_1 == user_id_2:
        return None

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
            return row['status']  # 'pending', 'accepted', 'rejected'
    finally:
        conn.close()
