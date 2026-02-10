from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for
from app.services.feed_service import FeedService

posts_bp = Blueprint('posts', __name__, url_prefix='/posts')

@posts_bp.route('/create', methods=['POST'])
def create_post():
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    
    content = request.form.get('content')
    image = request.files.get('image')
    
    if FeedService.create_post(session['user_id'], content, image):
        pass # Success
    
    return redirect(url_for('pages.feed'))

@posts_bp.route('/<int:post_id>/like', methods=['POST'])
def like_post(post_id):
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    
    action = FeedService.toggle_like(post_id, session['user_id'])
    return jsonify({'success': True, 'action': action})

@posts_bp.route('/<int:post_id>/comment', methods=['POST'])
def comment_post(post_id):
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    content = data.get('content')
    
    comment_id = FeedService.add_comment(post_id, session['user_id'], content)
    if comment_id:
        # Return comment data for appending to DOM
        return jsonify({
            'success': True, 
            'comment_id': comment_id, 
            'user_name': session['full_name'],
            'content': content
        })
    return jsonify({'error': 'Failed'}), 500

@posts_bp.route('/<int:post_id>/comments')
def get_comments(post_id):
    comments = FeedService.get_post_comments(post_id)
    return jsonify(comments)
