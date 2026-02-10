"""
Posts and Feed routes blueprint.
Handles post creation, feed display, and AJAX interactions.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from functools import wraps
from app.services import post_service
from datetime import datetime

posts_bp = Blueprint('posts', __name__)


def login_required(f):
    """Decorator to require login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def api_login_required(f):
    """Decorator for API endpoints requiring login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function


# ========== PAGE ROUTES ==========

@posts_bp.route('/feed')
@login_required
def feed():
    """Display global feed page."""
    page = request.args.get('page', 1, type=int)
    user_id = session.get('user_id')
    
    posts = post_service.get_feed(page=page, current_user_id=user_id)
    
    # Get first post ID for auto-refresh
    first_post_id = posts[0]['post_id'] if posts else 0
    
    return render_template('feed/feed.html',
                           posts=posts,
                           page=page,
                           first_post_id=first_post_id)


@posts_bp.route('/posts/create', methods=['GET', 'POST'])
@login_required
def create_post():
    """Create a new post."""
    if request.method == 'POST':
        user_id = session.get('user_id')
        content = request.form.get('content', '').strip()
        image = request.files.get('image')
        
        success, result = post_service.create_post(user_id, content, image)
        
        if not success:
            flash(result, 'error')
            return render_template('feed/create_post.html', content=content)
        
        flash('Post created successfully!', 'success')
        return redirect(url_for('posts.feed'))
    
    return render_template('feed/create_post.html')


# ========== API ENDPOINTS ==========

@posts_bp.route('/api/posts/<int:post_id>/like', methods=['POST'])
@api_login_required
def toggle_like(post_id):
    """Toggle like on a post (AJAX)."""
    user_id = session.get('user_id')
    
    liked, likes_count = post_service.toggle_like(post_id, user_id)
    
    return jsonify({
        'success': True,
        'liked': liked,
        'likes_count': likes_count
    })


@posts_bp.route('/api/posts/<int:post_id>/comment', methods=['POST'])
@api_login_required
def add_comment(post_id):
    """Add comment to a post (AJAX)."""
    user_id = session.get('user_id')
    content = request.json.get('content', '') if request.is_json else request.form.get('content', '')
    
    comment = post_service.add_comment(post_id, user_id, content)
    
    if not comment:
        return jsonify({'error': 'Content is required'}), 400
    
    return jsonify({
        'success': True,
        'comment': {
            'comment_id': comment['comment_id'],
            'content': comment['content'],
            'full_name': comment['full_name'] or 'User',
            'profile_picture': comment['profile_picture'],
            'created_at': comment['created_at'].isoformat() if comment.get('created_at') else None
        }
    })


@posts_bp.route('/api/posts/<int:post_id>/comments', methods=['GET'])
def get_comments(post_id):
    """Get comments for a post (AJAX)."""
    comments = post_service.get_comments(post_id)
    
    return jsonify({
        'success': True,
        'comments': [{
            'comment_id': c['comment_id'],
            'content': c['content'],
            'full_name': c['full_name'] or 'User',
            'profile_picture': c['profile_picture'],
            'created_at': c['created_at'].isoformat() if c.get('created_at') else None
        } for c in comments]
    })


@posts_bp.route('/api/posts/<int:post_id>', methods=['DELETE'])
@api_login_required
def delete_post(post_id):
    """Delete a post (AJAX)."""
    user_id = session.get('user_id')
    
    success, message = post_service.delete_post(post_id, user_id)
    
    if not success:
        return jsonify({'error': message}), 403
    
    return jsonify({'success': True})


@posts_bp.route('/api/feed/new')
@api_login_required
def get_new_posts():
    """Get new posts since given ID (for auto-refresh)."""
    since_id = request.args.get('since', 0, type=int)
    user_id = session.get('user_id')
    
    posts = post_service.get_new_posts(since_id, user_id)
    
    return jsonify({
        'success': True,
        'count': len(posts),
        'posts': [{
            'post_id': p['post_id'],
            'author_id': p['author_id'],
            'content': p['content'],
            'image_path': p['image_path'],
            'created_at': p['created_at'].isoformat() if p.get('created_at') else None,
            'likes_count': p['likes_count'],
            'comments_count': p['comments_count'],
            'full_name': p['full_name'] or 'User',
            'profile_picture': p['profile_picture'],
            'headline': p['headline'],
            'liked_by_current_user': bool(p['liked_by_current_user'])
        } for p in posts]
    })
