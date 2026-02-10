from flask import Blueprint

recruiter_dashboard_bp = Blueprint('recruiter_dashboard', __name__)

from . import routes
