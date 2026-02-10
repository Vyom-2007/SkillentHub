from database.connection import get_db_connection

class Post:
    @staticmethod
    def create(author_id, content, image_path=None):
        conn = get_db_connection()
        if not conn: return False
        try:
            with conn.cursor() as cursor:
                sql = "INSERT INTO posts (author_id, content, image_path) VALUES (%s, %s, %s)"
                cursor.execute(sql, (author_id, content, image_path))
                post_id = cursor.lastrowid
            conn.commit()
            return post_id
        finally:
            conn.close()

    @staticmethod
    def get_feed(user_id, page=1, per_page=10):
        # Logic: Get posts from self AND accepted connections
        offset = (page - 1) * per_page
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Complex query for feed
                sql = """
                    SELECT p.*, u.full_name, pr.profile_picture, pr.headline,
                    (SELECT COUNT(*) FROM post_likes pl WHERE pl.post_id = p.post_id AND pl.user_id = %s) as is_liked,
                    (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.post_id) as comment_count
                    FROM posts p
                    JOIN users u ON p.author_id = u.user_id
                    LEFT JOIN profiles pr ON u.user_id = pr.user_id
                    WHERE p.author_id = %s
                    OR p.author_id IN (
                        SELECT user_id_1 FROM connections WHERE user_id_2 = %s AND status = 'accepted'
                        UNION
                        SELECT user_id_2 FROM connections WHERE user_id_1 = %s AND status = 'accepted'
                    )
                    ORDER BY p.created_at DESC
                    LIMIT %s OFFSET %s
                """
                cursor.execute(sql, (user_id, user_id, user_id, user_id, per_page, offset))
                return cursor.fetchall()
        finally:
            conn.close()

    @staticmethod
    def like(post_id, user_id):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Insert ignore or check exist
                cursor.execute("SELECT * FROM post_likes WHERE post_id=%s AND user_id=%s", (post_id, user_id))
                if cursor.fetchone():
                    # unlike
                    cursor.execute("DELETE FROM post_likes WHERE post_id=%s AND user_id=%s", (post_id, user_id))
                    action = 'unliked'
                else:
                    # like
                    cursor.execute("INSERT INTO post_likes (post_id, user_id) VALUES (%s, %s)", (post_id, user_id))
                    action = 'liked'
                
                # Update count
                cursor.execute("""
                    UPDATE posts SET likes_count = (SELECT COUNT(*) FROM post_likes WHERE post_id=%s) 
                    WHERE post_id=%s
                """, (post_id, post_id))
            conn.commit()
            return action
        except Exception as e:
            print(f"Like error: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def add_comment(post_id, user_id, content):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                sql = "INSERT INTO comments (post_id, user_id, content) VALUES (%s, %s, %s)"
                cursor.execute(sql, (post_id, user_id, content))
                comment_id = cursor.lastrowid
            conn.commit()
            return comment_id
        finally:
            conn.close()

    @staticmethod
    def get_comments(post_id):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                    SELECT c.*, u.full_name, pr.profile_picture 
                    FROM comments c
                    JOIN users u ON c.user_id = u.user_id
                    LEFT JOIN profiles pr ON u.user_id = pr.user_id
                    WHERE c.post_id = %s
                    ORDER BY c.created_at ASC
                """
                cursor.execute(sql, (post_id,))
                return cursor.fetchall()
        finally:
            conn.close()
