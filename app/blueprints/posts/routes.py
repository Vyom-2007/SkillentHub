from flask import (
    render_template, request, redirect, url_for,
    session, flash, jsonify,
)
from app.blueprints.posts import posts_bp
from app.utils.decorators import login_required
from app.services.post_service import (
    get_feed,
    get_new_posts_count,
    create_post,
    delete_post,
    toggle_like,
    get_comments,
    add_comment,
    save_post_image,
)


# ──────────────────────────────────────────────────────────
# Feed
# ──────────────────────────────────────────────────────────

@posts_bp.route('/feed', methods=['GET'])
@login_required
def feed():
    user_id = session['user_id']
    offset = request.args.get('offset', 0, type=int)
    posts = get_feed(offset, user_id)
    return render_template('feed/feed.html', posts=posts, offset=offset)


@posts_bp.route('/feed/new', methods=['GET'])
@login_required
def feed_new():
    since_id = request.args.get('since', 0, type=int)
    count = get_new_posts_count(since_id)
    return jsonify({'new_count': count})


# ──────────────────────────────────────────────────────────
# Create Post
# ──────────────────────────────────────────────────────────

@posts_bp.route('/posts/create', methods=['POST'])
@login_required
def post_create():
    user_id = session['user_id']
    content = request.form.get('content', '').strip()

    # Handle image upload
    image_path = None
    img_file = request.files.get('image')
    has_image = img_file and img_file.filename

    # Validate: need either content or image
    if not content and not has_image:
        flash('Post must have text or an image.', 'danger')
        return redirect(url_for('posts.feed'))

    if has_image:
        try:
            image_path = save_post_image(img_file)
        except ValueError as e:
            flash(str(e), 'danger')
            return redirect(url_for('posts.feed'))

    create_post(user_id, 'user', content, image_path)
    flash('Post created!', 'success')
    return redirect(url_for('posts.feed'))


# ──────────────────────────────────────────────────────────
# Like / Unlike
# ──────────────────────────────────────────────────────────

@posts_bp.route('/posts/<int:post_id>/like', methods=['POST'])
@login_required
def post_like(post_id):
    user_id = session['user_id']
    result = toggle_like(post_id, user_id)
    return jsonify(result)


# ──────────────────────────────────────────────────────────
# Comments
# ──────────────────────────────────────────────────────────

@posts_bp.route('/posts/<int:post_id>/comments', methods=['GET'])
@login_required
def post_comments(post_id):
    comments = get_comments(post_id)
    # Serialize datetimes
    out = []
    for c in comments:
        out.append({
            'comment_id': c['comment_id'],
            'content': c['content'],
            'full_name': c['full_name'],
            'profile_picture': c['profile_picture'],
            'created_at': c['created_at'].isoformat() if c['created_at'] else '',
        })
    return jsonify(out)


@posts_bp.route('/posts/<int:post_id>/comments', methods=['POST'])
@login_required
def post_comment_create(post_id):
    user_id = session['user_id']
    data = request.get_json(silent=True) or {}
    content = data.get('content', '').strip()

    if not content:
        return jsonify({'error': 'Comment cannot be empty.'}), 400

    if len(content) > 500:
        return jsonify({'error': 'Comment must be under 500 characters.'}), 400

    comment = add_comment(post_id, user_id, content)
    if not comment:
        return jsonify({'error': 'Failed to add comment.'}), 500

    return jsonify({
        'comment_id': comment['comment_id'],
        'content': comment['content'],
        'full_name': comment['full_name'],
        'profile_picture': comment['profile_picture'],
        'created_at': comment['created_at'].isoformat() if comment['created_at'] else '',
    }), 201


# ──────────────────────────────────────────────────────────
# Delete Post
# ──────────────────────────────────────────────────────────

@posts_bp.route('/posts/<int:post_id>', methods=['DELETE'])
@login_required
def post_delete(post_id):
    user_id = session['user_id']
    deleted = delete_post(post_id, user_id)
    if deleted:
        return jsonify({'status': 'deleted'})
    return jsonify({'error': 'Not found or not authorized.'}), 403
