"""
Static pages routes blueprint for landing, about, and contact pages.
"""

from flask import Blueprint, render_template, redirect, url_for, session


# Create the pages blueprint
pages_bp = Blueprint('pages', __name__)


@pages_bp.route('/')
def index():
    """
    Home/Landing page.
    Redirects to dashboard if user is logged in, otherwise shows landing page.
    """
    if session.get('user_id'):
        return redirect(url_for('dashboard.index'))
    
    return render_template('pages/index.html')


@pages_bp.route('/about')
def about():
    """About page."""
    return render_template('pages/about.html')


@pages_bp.route('/contact')
def contact():
    """Contact page."""
    return render_template('pages/contact.html')
