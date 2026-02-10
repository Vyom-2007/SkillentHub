from flask import Blueprint, render_template, session
from app.models.application import Application
from app.utils.decorators import login_required

applications_bp = Blueprint('applications', __name__)

@applications_bp.route('/mine')
@login_required
def mine():
    user_id = session['user_id']
    applications = Application.get_by_user(user_id)
    return render_template('applications/mine.html', applications=applications)
