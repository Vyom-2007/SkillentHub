from flask import Blueprint, render_template, request, jsonify, session
from app.models.post import Post, PostLike
from app.utils.decorators import login_required

feed_bp = Blueprint('feed', __name__)

@feed_bp.route('/')
@login_required
def index():
    posts = Post.get_feed(limit=10)
    
    # Process posts to add 'is_liked' flag for current user
    user_id = session.get('user_id')
    if user_id:
        for post in posts:
            post['is_liked'] = PostLike.has_liked(post['post_id'], user_id)
            
    return render_template('feed/index.html', posts=posts)

@feed_bp.route('/new')
@login_required
def get_new_posts():
    since_id = request.args.get('since', type=int)
    posts = Post.get_feed(limit=10, since_id=since_id)
    
    # Return HTML snippets or JSON data?
    # Prompt implies JSON for auto-refresh: "/api/feed/new?since={last_post_id}, banner 'X new posts available'"
    # So we return count or data. 
    # Let's return the data so frontend can prepend or show banner.
    # Actually, returning JSON data is cleaner.
    
    # Format dates
    for post in posts:
        post['created_at'] = post['created_at'].isoformat()
        
    return jsonify({'status': 'success', 'posts': posts, 'count': len(posts)})
