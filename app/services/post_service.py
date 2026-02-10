"""
Post management service.
Handles post CRUD, likes, comments, and feed queries.
"""
import os
import uuid
from datetime import datetime
from flask import current_app
from app.database.connection import execute_query, execute_insert, get_db_connection


# ========== FILE UPLOAD HELPERS ==========

ALLOWED_POST_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}
MAX_POST_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB


def save_post_image(file):
    """Save uploaded post image. Returns (success, filename_or_error)."""
    if not file or not file.filename:
        return True, None  # No file is OK
    
    # Check extension
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_POST_EXTENSIONS:
        return False, 'Only JPG, PNG, GIF allowed'
    
    # Check size
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    
    if size > MAX_POST_IMAGE_SIZE:
        return False, 'File size exceeds 10MB limit'
    
    # Generate unique filename
    filename = f"post_{uuid.uuid4().hex[:12]}.{ext}"
    
    # Ensure upload directory exists
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'posts')
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save file
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)
    
    return True, filename


def delete_post_image(filename):
    """Delete post image from disk."""
    if not filename:
        return
    
    filepath = os.path.join(current_app.root_path, 'static', 'uploads', 'posts', filename)
    if os.path.exists(filepath):
        os.remove(filepath)


# ========== POST CRUD ==========

def create_post(author_id, content, image_file=None):
    """Create a new post. Returns (success, post_id_or_error)."""
    if not content or len(content.strip()) == 0:
        return False, 'Content is required'
    
    if len(content) > 5000:
        return False, 'Content exceeds 5000 characters'
    
    # Handle image upload
    image_path = None
    if image_file and image_file.filename:
        success, result = save_post_image(image_file)
        if not success:
            return False, result
        image_path = result
    
    # Insert post
    query = """
        INSERT INTO posts (author_id, content, image_path)
        VALUES (%s, %s, %s)
    """
    post_id = execute_insert(query, (author_id, content.strip(), image_path))
    
    return True, post_id


def get_post(post_id):
    """Get single post by ID."""
    query = """
        SELECT p.*, u.email, pr.full_name, pr.profile_picture, pr.headline
        FROM posts p
        JOIN users u ON p.author_id = u.user_id
        LEFT JOIN profiles pr ON p.author_id = pr.user_id
        WHERE p.post_id = %s
    """
    return execute_query(query, (post_id,), fetch_one=True)


def delete_post(post_id, user_id):
    """Delete a post. Only author can delete. Returns (success, message)."""
    # Check ownership
    post = execute_query(
        "SELECT author_id, image_path FROM posts WHERE post_id = %s",
        (post_id,), fetch_one=True
    )
    
    if not post:
        return False, 'Post not found'
    
    if post['author_id'] != user_id:
        return False, 'Unauthorized'
    
    # Delete image file
    if post.get('image_path'):
        delete_post_image(post['image_path'])
    
    # Delete comments and likes first
    execute_query("DELETE FROM post_comments WHERE post_id = %s", (post_id,))
    execute_query("DELETE FROM post_likes WHERE post_id = %s", (post_id,))
    
    # Delete post
    execute_query("DELETE FROM posts WHERE post_id = %s", (post_id,))
    
    return True, 'Post deleted'


# ========== FEED QUERIES ==========

def get_feed(page=1, per_page=50, current_user_id=None):
    """Get global feed with pagination."""
    offset = (page - 1) * per_page
    
    query = """
        SELECT 
            p.post_id, p.author_id, p.content, p.image_path, 
            p.created_at, p.likes_count,
            u.email,
            pr.full_name, pr.profile_picture, pr.headline,
            (SELECT COUNT(*) FROM post_comments WHERE post_id = p.post_id) as comments_count,
            EXISTS(
                SELECT 1 FROM post_likes 
                WHERE post_id = p.post_id AND user_id = %s
            ) as liked_by_current_user
        FROM posts p
        JOIN users u ON p.author_id = u.user_id
        LEFT JOIN profiles pr ON p.author_id = pr.user_id
        ORDER BY p.created_at DESC
        LIMIT %s OFFSET %s
    """
    
    posts = execute_query(query, (current_user_id or 0, per_page, offset), fetch_all=True)
    return posts or []


def get_new_posts(since_id, current_user_id=None):
    """Get posts newer than given ID."""
    query = """
        SELECT 
            p.post_id, p.author_id, p.content, p.image_path, 
            p.created_at, p.likes_count,
            u.email,
            pr.full_name, pr.profile_picture, pr.headline,
            (SELECT COUNT(*) FROM post_comments WHERE post_id = p.post_id) as comments_count,
            EXISTS(
                SELECT 1 FROM post_likes 
                WHERE post_id = p.post_id AND user_id = %s
            ) as liked_by_current_user
        FROM posts p
        JOIN users u ON p.author_id = u.user_id
        LEFT JOIN profiles pr ON p.author_id = pr.user_id
        WHERE p.post_id > %s
        ORDER BY p.created_at DESC
        LIMIT 50
    """
    
    posts = execute_query(query, (current_user_id or 0, since_id), fetch_all=True)
    return posts or []


# ========== LIKES ==========

def toggle_like(post_id, user_id):
    """Toggle like on a post. Returns (liked, new_likes_count)."""
    # Check if already liked
    existing = execute_query(
        "SELECT like_id FROM post_likes WHERE post_id = %s AND user_id = %s",
        (post_id, user_id), fetch_one=True
    )
    
    connection = get_db_connection()
    with connection.cursor() as cursor:
        if existing:
            # Unlike
            cursor.execute(
                "DELETE FROM post_likes WHERE post_id = %s AND user_id = %s",
                (post_id, user_id)
            )
            cursor.execute(
                "UPDATE posts SET likes_count = GREATEST(likes_count - 1, 0) WHERE post_id = %s",
                (post_id,)
            )
            liked = False
        else:
            # Like
            cursor.execute(
                "INSERT INTO post_likes (post_id, user_id) VALUES (%s, %s)",
                (post_id, user_id)
            )
            cursor.execute(
                "UPDATE posts SET likes_count = likes_count + 1 WHERE post_id = %s",
                (post_id,)
            )
            liked = True
    
    # Get updated count
    result = execute_query(
        "SELECT likes_count FROM posts WHERE post_id = %s",
        (post_id,), fetch_one=True
    )
    
    return liked, result['likes_count'] if result else 0


# ========== COMMENTS ==========

def add_comment(post_id, user_id, content):
    """Add a comment to a post. Returns comment dict or None."""
    if not content or len(content.strip()) == 0:
        return None
    
    if len(content) > 5000:
        content = content[:5000]
    
    comment_id = execute_insert(
        "INSERT INTO post_comments (post_id, user_id, content) VALUES (%s, %s, %s)",
        (post_id, user_id, content.strip())
    )
    
    # Get the comment with author info
    query = """
        SELECT c.*, pr.full_name, pr.profile_picture
        FROM post_comments c
        LEFT JOIN profiles pr ON c.user_id = pr.user_id
        WHERE c.comment_id = %s
    """
    return execute_query(query, (comment_id,), fetch_one=True)


def get_comments(post_id, limit=50):
    """Get comments for a post."""
    query = """
        SELECT c.*, pr.full_name, pr.profile_picture
        FROM post_comments c
        LEFT JOIN profiles pr ON c.user_id = pr.user_id
        WHERE c.post_id = %s
        ORDER BY c.created_at ASC
        LIMIT %s
    """
    return execute_query(query, (post_id, limit), fetch_all=True) or []


def get_comment_count(post_id):
    """Get comment count for a post."""
    result = execute_query(
        "SELECT COUNT(*) as count FROM post_comments WHERE post_id = %s",
        (post_id,), fetch_one=True
    )
    return result['count'] if result else 0
