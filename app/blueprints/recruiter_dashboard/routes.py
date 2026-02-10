from flask import Blueprint, render_template
from app.utils.decorators import recruiter_login_required

recruiter_dashboard_bp = Blueprint('recruiter_dashboard', __name__)

@recruiter_dashboard_bp.route('/')
@recruiter_login_required
def index():
    return render_template('recruiter/dashboard.html')
