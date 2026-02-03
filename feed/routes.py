"""
Feed routes blueprint for global feed, likes, and comments.
"""

from functools import wraps

from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from database.db import execute_query


# Create the feed blueprint
feed_bp = Blueprint('feed', __name__, url_prefix='/feed')


def login_required(f):
    """Decorator to require user login for protected routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@feed_bp.route('/')
def global_feed():
    """
    Display the global feed with all posts.
    Includes author info, like counts, comment counts, and user's like status.
    """
    current_user_id = session.get('user_id')
    
    # Main query to fetch posts with author info, like count, comment count, and user's like status
    if current_user_id:
        # Logged-in user: include like status
        posts = execute_query(
            """
            SELECT 
                p.id,
                p.user_id,
                p.content,
                p.image_url,
                p.project_link,
                p.created_at,
                u.full_name,
                u.profile_pic,
                (SELECT COUNT(*) FROM likes WHERE post_id = p.id) AS like_count,
                (SELECT COUNT(*) FROM comments WHERE post_id = p.id) AS comment_count,
                (SELECT COUNT(*) FROM likes WHERE post_id = p.id AND user_id = %s) AS user_liked
            FROM posts p
            INNER JOIN users u ON p.user_id = u.id
            ORDER BY p.created_at DESC
            """,
            (current_user_id,),
            fetch_all=True
        )
    else:
        # Guest user: no like status needed
        posts = execute_query(
            """
            SELECT 
                p.id,
                p.user_id,
                p.content,
                p.image_url,
                p.project_link,
                p.created_at,
                u.full_name,
                u.profile_pic,
                (SELECT COUNT(*) FROM likes WHERE post_id = p.id) AS like_count,
                (SELECT COUNT(*) FROM comments WHERE post_id = p.id) AS comment_count,
                0 AS user_liked
            FROM posts p
            INNER JOIN users u ON p.user_id = u.id
            ORDER BY p.created_at DESC
            """,
            fetch_all=True
        )
    
    # Fetch comments for each post (last 3 comments per post)
    posts_with_comments = []
    for post in posts or []:
        comments = execute_query(
            """
            SELECT c.id, c.content, c.created_at, u.full_name, u.profile_pic
            FROM comments c
            INNER JOIN users u ON c.user_id = u.id
            WHERE c.post_id = %s
            ORDER BY c.created_at DESC
            LIMIT 3
            """,
            (post['id'],),
            fetch_all=True
        )
        post_dict = dict(post)
        post_dict['comments'] = comments or []
        posts_with_comments.append(post_dict)
    
    return render_template('feed/global_feed.html', posts=posts_with_comments)


@feed_bp.route('/like/<int:post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    """
    Toggle like on a post.
    If already liked, unlike it. Otherwise, like it.
    """
    user_id = session['user_id']
    
    # Check if user already liked this post
    existing_like = execute_query(
        "SELECT * FROM likes WHERE user_id = %s AND post_id = %s",
        (user_id, post_id),
        fetch_one=True
    )
    
    if existing_like:
        # Unlike: Delete the like
        execute_query(
            "DELETE FROM likes WHERE user_id = %s AND post_id = %s",
            (user_id, post_id),
            commit=True
        )
    else:
        # Like: Insert new like
        execute_query(
            "INSERT INTO likes (user_id, post_id, created_at) VALUES (%s, %s, NOW())",
            (user_id, post_id),
            commit=True
        )
    
    # Redirect back to the referring page or feed
    referrer = request.referrer
    if referrer:
        return redirect(referrer)
    return redirect(url_for('feed.global_feed'))


@feed_bp.route('/comment/<int:post_id>', methods=['POST'])
@login_required
def add_comment(post_id):
    """
    Add a comment to a post.
    """
    user_id = session['user_id']
    content = request.form.get('content', '').strip()
    
    # Validate content
    if not content:
        flash('Comment cannot be empty.', 'warning')
    else:
        # Insert comment into database
        result = execute_query(
            "INSERT INTO comments (user_id, post_id, content, created_at) VALUES (%s, %s, %s, NOW())",
            (user_id, post_id, content),
            commit=True
        )
        
        if result is not None:
            flash('Comment added successfully!', 'success')
        else:
            flash('Failed to add comment. Please try again.', 'danger')
    
    # Redirect back to the referring page or feed
    referrer = request.referrer
    if referrer:
        return redirect(referrer)
    return redirect(url_for('feed.global_feed'))


@feed_bp.route('/post/<int:post_id>/comments')
def view_comments(post_id):
    """
    View all comments for a specific post.
    """
    # Fetch post info
    post = execute_query(
        """
        SELECT p.*, u.full_name, u.profile_pic
        FROM posts p
        INNER JOIN users u ON p.user_id = u.id
        WHERE p.id = %s
        """,
        (post_id,),
        fetch_one=True
    )
    
    if not post:
        flash('Post not found.', 'danger')
        return redirect(url_for('feed.global_feed'))
    
    # Fetch all comments
    comments = execute_query(
        """
        SELECT c.id, c.content, c.created_at, c.user_id, u.full_name, u.profile_pic
        FROM comments c
        INNER JOIN users u ON c.user_id = u.id
        WHERE c.post_id = %s
        ORDER BY c.created_at DESC
        """,
        (post_id,),
        fetch_all=True
    )
    
    return render_template('feed/comments.html', post=post, comments=comments or [])
