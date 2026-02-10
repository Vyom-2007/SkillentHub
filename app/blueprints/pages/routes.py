from flask import render_template
from app.blueprints.pages import pages_bp


@pages_bp.route('/')
def landing():
    return render_template('auth/landing.html')
