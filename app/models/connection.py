from database.connection import get_db_connection

class Connection:
    @staticmethod
    def create(user_id_1, user_id_2, created_by):
        conn = get_db_connection()
        if not conn: return False
        try:
            # Sort IDs
            u1, u2 = sorted([user_id_1, user_id_2])
            with conn.cursor() as cursor:
                sql = "INSERT INTO connections (user_id_1, user_id_2, status, created_by) VALUES (%s, %s, 'pending', %s)"
                cursor.execute(sql, (u1, u2, created_by))
            conn.commit()
            return True
        except Exception as e:
            print(f"Connection creation error: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def get_status(user1, user2):
        conn = get_db_connection()
        if not conn: return None
        try:
            u1, u2 = sorted([user1, user2])
            with conn.cursor() as cursor:
                sql = "SELECT status, created_by FROM connections WHERE user_id_1 = %s AND user_id_2 = %s"
                cursor.execute(sql, (u1, u2))
                return cursor.fetchone()
        finally:
            conn.close()

    @staticmethod
    def get_pending_requests(user_id):
        conn = get_db_connection()
        if not conn: return []
        try:
            with conn.cursor() as cursor:
                # Users who sent me a request (I am user_id)
                # If I am user_id, and created_by != user_id, and status='pending'
                # The row has user_id_1 and user_id_2. One of them is me.
                # If created_by != me, check if I am the other one.
                sql = """
                    SELECT c.connection_id, u.user_id, u.full_name, p.profile_picture, p.headline
                    FROM connections c
                    JOIN users u ON (u.user_id = CASE WHEN c.user_id_1 = %s THEN c.user_id_2 ELSE c.user_id_1 END)
                    LEFT JOIN profiles p ON u.user_id = p.user_id
                    WHERE (c.user_id_1 = %s OR c.user_id_2 = %s)
                    AND c.status = 'pending'
                    AND c.created_by != %s
                """
                cursor.execute(sql, (user_id, user_id, user_id, user_id))
                return cursor.fetchall()
        finally:
            conn.close()

    @staticmethod
    def accept(connection_id, user_id):
        conn = get_db_connection()
        if not conn: return False
        try:
            with conn.cursor() as cursor:
                # Verify it is for me
                sql_check = "SELECT * FROM connections WHERE connection_id = %s"
                cursor.execute(sql_check, (connection_id,))
                conn_row = cursor.fetchone()
                if not conn_row: return False
                
                # Check if I am the receiver (not created_by)
                if conn_row['created_by'] == user_id: return False
                
                sql = "UPDATE connections SET status = 'accepted', responded_at = CURRENT_TIMESTAMP WHERE connection_id = %s"
                cursor.execute(sql, (connection_id,))
            conn.commit()
            return True
        finally:
            conn.close()
