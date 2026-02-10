from app.models.post import Post
from flask import current_app
from werkzeug.utils import secure_filename
import os
from database.connection import get_db_connection
from app.services.notification_service import NotificationService
    @staticmethod
    def create_post(user_id, content, image_file=None):
        image_path = None
        if image_file and image_file.filename:
            filename = secure_filename(f"post_{user_id}_{image_file.filename}")
            image_file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], 'posts', filename))
            image_path = f"posts/{filename}"
            
        return Post.create(user_id, content, image_path)

    @staticmethod
    def get_user_feed(user_id):
        # We can implement pagination logic here
        return Post.get_feed(user_id)
        
from app.services.notification_service import NotificationService
from app.models.post import Post # Re-import to be safe or use existing

    @staticmethod
    def toggle_like(post_id, user_id):
        action = Post.like(post_id, user_id)
        if action == 'liked':
            # Get post author
            conn = get_db_connection()
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT author_id FROM posts WHERE post_id = %s", (post_id,))
                    res = cursor.fetchone()
                    if res and res['author_id'] != user_id:
                        NotificationService.create_notification(
                            res['author_id'], 'post_like', 
                            'Someone liked your post.', post_id
                        )
            finally:
                conn.close()
        return action
        
    @staticmethod
    def add_comment(post_id, user_id, content):
        comment_id = Post.add_comment(post_id, user_id, content)
        if comment_id:
             # Get post author
            conn = get_db_connection()
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT author_id FROM posts WHERE post_id = %s", (post_id,))
                    res = cursor.fetchone()
                    if res and res['author_id'] != user_id:
                        NotificationService.create_notification(
                            res['author_id'], 'post_comment', 
                            'Someone commented on your post.', post_id
                        )
            finally:
                conn.close()
        return comment_id
        
    @staticmethod
    def get_post_comments(post_id):
        return Post.get_comments(post_id)
