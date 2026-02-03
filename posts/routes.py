"""
Posts routes blueprint.
"""

import os
import time
from functools import wraps

from flask import Blueprint, render_template, redirect, url_for, flash, session, request, abort, current_app
from werkzeug.utils import secure_filename

from database.db import execute_query
from posts.forms import PostForm


# Create the posts blueprint
posts_bp = Blueprint('posts', __name__, url_prefix='/posts')


def login_required(f):
    """Decorator to require user login for protected routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def get_unique_filename(original_filename, user_id, prefix=''):
    """
    Generate a unique filename by appending user_id and timestamp.
    """
    filename = secure_filename(original_filename)
    name, ext = os.path.splitext(filename)
    timestamp = int(time.time())
    return f"{prefix}{user_id}_{timestamp}{ext}"


def save_post_image(file, user_id):
    """
    Save an uploaded post image to static/uploads/posts/.
    
    Returns:
        str: The saved filename, or None if no file was uploaded.
    """
    if file and file.filename:
        filename = get_unique_filename(file.filename, user_id, prefix='post_')
        
        # Ensure upload directory exists
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'posts')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save the file
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        return filename
    return None


def delete_post_image(filename):
    """Delete a post image from the uploads directory."""
    if filename:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'posts', filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass


@posts_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new post."""
    form = PostForm()
    
    if form.validate_on_submit():
        user_id = session['user_id']
        content = form.content.data.strip()
        project_link = form.project_link.data.strip() if form.project_link.data else None
        
        # Handle image upload
        image_filename = None
        if form.image.data and form.image.data.filename:
            image_filename = save_post_image(form.image.data, user_id)
        
        # Insert post into database
        result = execute_query(
            """
            INSERT INTO posts (user_id, content, image_url, project_link, created_at) 
            VALUES (%s, %s, %s, %s, NOW())
            """,
            (user_id, content, image_filename, project_link),
            commit=True
        )
        
        if result is not None:
            flash('Post created successfully!', 'success')
            return redirect(url_for('profile.view_profile', user_id=user_id))
        else:
            flash('An error occurred while creating your post. Please try again.', 'danger')
    
    return render_template('posts/create.html', form=form)


@posts_bp.route('/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit(post_id):
    """Edit an existing post."""
    user_id = session['user_id']
    
    # Fetch post from database
    post = execute_query(
        "SELECT * FROM posts WHERE id = %s",
        (post_id,),
        fetch_one=True
    )
    
    # Check if post exists
    if not post:
        abort(404, description="Post not found")
    
    # Ownership check - verify user owns this post
    if post['user_id'] != user_id:
        abort(403, description="You don't have permission to edit this post")
    
    form = PostForm()
    
    if request.method == 'GET':
        # Pre-fill form with current data
        form.content.data = post.get('content', '')
        form.project_link.data = post.get('project_link', '')
    
    if form.validate_on_submit():
        content = form.content.data.strip()
        project_link = form.project_link.data.strip() if form.project_link.data else None
        
        # Handle image upload
        image_filename = post.get('image_url')  # Keep existing if no new upload
        
        if form.image.data and form.image.data.filename:
            # Delete old image if exists
            if image_filename:
                delete_post_image(image_filename)
            
            # Save new image
            image_filename = save_post_image(form.image.data, user_id)
        
        # Update post in database
        result = execute_query(
            """
            UPDATE posts 
            SET content = %s, image_url = %s, project_link = %s 
            WHERE id = %s
            """,
            (content, image_filename, project_link, post_id),
            commit=True
        )
        
        if result is not None:
            flash('Post updated successfully!', 'success')
            return redirect(url_for('profile.view_profile', user_id=user_id))
        else:
            flash('An error occurred while updating your post. Please try again.', 'danger')
    
    return render_template('posts/edit.html', form=form, post=post)


@posts_bp.route('/delete/<int:post_id>', methods=['POST'])
@login_required
def delete(post_id):
    """Delete a post."""
    user_id = session['user_id']
    
    # Fetch post from database
    post = execute_query(
        "SELECT * FROM posts WHERE id = %s",
        (post_id,),
        fetch_one=True
    )
    
    # Check if post exists
    if not post:
        flash('Post not found.', 'danger')
        return redirect(url_for('profile.view_profile', user_id=user_id))
    
    # Ownership check - verify user owns this post
    if post['user_id'] != user_id:
        abort(403, description="You don't have permission to delete this post")
    
    # Delete associated image if exists
    if post.get('image_url'):
        delete_post_image(post['image_url'])
    
    # Delete post from database
    result = execute_query(
        "DELETE FROM posts WHERE id = %s",
        (post_id,),
        commit=True
    )
    
    if result is not None:
        flash('Post deleted successfully!', 'success')
    else:
        flash('An error occurred while deleting your post.', 'danger')
    
    return redirect(url_for('profile.view_profile', user_id=user_id))


@posts_bp.route('/view/<int:post_id>')
def view(post_id):
    """View a single post."""
    post = execute_query(
        """
        SELECT p.*, u.full_name, u.profile_pic 
        FROM posts p 
        JOIN users u ON p.user_id = u.id 
        WHERE p.id = %s
        """,
        (post_id,),
        fetch_one=True
    )
    
    if not post:
        abort(404, description="Post not found")
    
    is_owner = session.get('user_id') == post['user_id']
    
    return render_template('posts/view.html', post=post, is_owner=is_owner)


@posts_bp.errorhandler(403)
def forbidden_error(error):
    """Handle 403 errors."""
    flash('You don\'t have permission to perform this action.', 'danger')
    return redirect(url_for('dashboard.index'))


@posts_bp.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors for posts routes."""
    from flask import render_template
    return render_template('errors/404.html', message="Post not found."), 404
