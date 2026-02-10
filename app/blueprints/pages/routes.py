from flask import Blueprint, render_template, session, redirect, url_for
from app.services.auth_service import AuthService
from app.services.feed_service import FeedService

pages_bp = Blueprint('pages', __name__)

@pages_bp.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('pages.feed'))
    return render_template('pages/index.html')

@pages_bp.route('/feed')
def feed():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user = AuthService.get_current_user()
    posts = FeedService.get_user_feed(user['user_id'])
    return render_template('feed/index.html', user=user, posts=posts)
