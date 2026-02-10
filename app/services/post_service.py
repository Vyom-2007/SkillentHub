import os
import uuid
from PIL import Image
from flask import current_app
from app.database.connection import get_db_connection


ALLOWED_POST_IMG_EXT = {'jpg', 'jpeg', 'png', 'gif'}
MAX_POST_IMG_SIZE = 10 * 1024 * 1024  # 10 MB


# ── Feed ──────────────────────────────────────────────────────

def get_feed(offset, current_user_id):
    """
    Fetch paginated feed: UNION ALL of user-posts + recruiter-posts.
    Returns list of dicts with author info and is_liked flag.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            sql = """
                SELECT
                    p.post_id, p.content, p.image_path, p.created_at,
                    p.likes_count, p.author_id, p.author_type,
                    u.full_name  AS author_name,
                    pr.profile_picture AS author_pic,
                    (SELECT COUNT(*) FROM post_likes pl
                     WHERE pl.post_id = p.post_id AND pl.user_id = %s) AS is_liked
                FROM posts p
                JOIN users u ON p.author_id = u.user_id
                LEFT JOIN profiles pr ON p.author_id = pr.user_id
                WHERE p.author_type = 'user'

                UNION ALL

                SELECT
                    p.post_id, p.content, p.image_path, p.created_at,
                    p.likes_count, p.author_id, p.author_type,
                    r.full_name  AS author_name,
                    rp.profile_picture AS author_pic,
                    (SELECT COUNT(*) FROM post_likes pl
                     WHERE pl.post_id = p.post_id AND pl.user_id = %s) AS is_liked
                FROM posts p
                JOIN recruiters r ON p.author_id = r.recruiter_id
                LEFT JOIN recruiter_profiles rp ON p.author_id = rp.recruiter_id
                WHERE p.author_type = 'recruiter'

                ORDER BY created_at DESC
                LIMIT 10 OFFSET %s
            """
            cur.execute(sql, (current_user_id, current_user_id, offset))
            return cur.fetchall()
    finally:
        conn.close()


def get_new_posts_count(since_id):
    """Count posts created after the given post_id."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS cnt FROM posts WHERE post_id > %s",
                (since_id,),
            )
            row = cur.fetchone()
            return row['cnt'] if row else 0
    finally:
        conn.close()


# ── Create / Delete ───────────────────────────────────────────

def create_post(author_id, author_type, content, image_path=None):
    """Insert a new post and return the post_id."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO posts (author_id, author_type, content, image_path) "
                "VALUES (%s, %s, %s, %s)",
                (author_id, author_type, content, image_path),
            )
            return cur.lastrowid
    finally:
        conn.close()


def delete_post(post_id, user_id):
    """Delete a post only if the current user is the author."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM posts WHERE post_id = %s "
                "AND author_id = %s AND author_type = 'user'",
                (post_id, user_id),
            )
            return cur.rowcount > 0
    finally:
        conn.close()


# ── Likes ─────────────────────────────────────────────────────

def toggle_like(post_id, user_id):
    """
    Like if not already liked, unlike if already liked.
    Returns { 'liked': bool, 'count': int }.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Check current state
            cur.execute(
                "SELECT like_id FROM post_likes "
                "WHERE post_id = %s AND user_id = %s",
                (post_id, user_id),
            )
            existing = cur.fetchone()

            if existing:
                # Unlike
                cur.execute(
                    "DELETE FROM post_likes WHERE post_id = %s AND user_id = %s",
                    (post_id, user_id),
                )
                cur.execute(
                    "UPDATE posts SET likes_count = GREATEST(likes_count - 1, 0) "
                    "WHERE post_id = %s",
                    (post_id,),
                )
                liked = False
            else:
                # Like
                cur.execute(
                    "INSERT INTO post_likes (post_id, user_id) VALUES (%s, %s)",
                    (post_id, user_id),
                )
                cur.execute(
                    "UPDATE posts SET likes_count = likes_count + 1 WHERE post_id = %s",
                    (post_id,),
                )
                liked = True

            # Get updated count
            cur.execute(
                "SELECT likes_count FROM posts WHERE post_id = %s",
                (post_id,),
            )
            row = cur.fetchone()
            count = row['likes_count'] if row else 0

            return {'liked': liked, 'count': count}
    finally:
        conn.close()


# ── Comments ──────────────────────────────────────────────────

def get_comments(post_id):
    """Fetch all comments for a post, oldest first, with user info."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT c.comment_id, c.content, c.created_at, "
                "       u.full_name, p.profile_picture "
                "FROM comments c "
                "JOIN users u ON c.user_id = u.user_id "
                "LEFT JOIN profiles p ON c.user_id = p.user_id "
                "WHERE c.post_id = %s "
                "ORDER BY c.created_at ASC",
                (post_id,),
            )
            return cur.fetchall()
    finally:
        conn.close()


def add_comment(post_id, user_id, content):
    """Insert a comment and return the new comment with user details."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO comments (post_id, user_id, content) "
                "VALUES (%s, %s, %s)",
                (post_id, user_id, content),
            )
            comment_id = cur.lastrowid

            # Fetch the newly created comment with user info
            cur.execute(
                "SELECT c.comment_id, c.content, c.created_at, "
                "       u.full_name, p.profile_picture "
                "FROM comments c "
                "JOIN users u ON c.user_id = u.user_id "
                "LEFT JOIN profiles p ON c.user_id = p.user_id "
                "WHERE c.comment_id = %s",
                (comment_id,),
            )
            return cur.fetchone()
    finally:
        conn.close()


# ── Image Handling ────────────────────────────────────────────

def save_post_image(file):
    """Validate and save a post image. Returns relative path."""
    if not file or not file.filename:
        return None

    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_POST_IMG_EXT:
        raise ValueError('Only JPG, PNG, and GIF images are allowed.')

    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > MAX_POST_IMG_SIZE:
        raise ValueError('Image must be under 10 MB.')

    # Validate with Pillow
    try:
        img = Image.open(file)
        img.verify()
        file.seek(0)
    except Exception:
        raise ValueError('Invalid image file.')

    filename = f"post_{uuid.uuid4().hex[:12]}.{ext}"
    upload_dir = os.path.join(current_app.root_path, '..', 'uploads', 'posts')
    os.makedirs(upload_dir, exist_ok=True)

    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)

    return f"uploads/posts/{filename}"
