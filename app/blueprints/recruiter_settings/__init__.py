from flask import Blueprint

recruiter_settings_bp = Blueprint('recruiter_settings', __name__)

from . import routes
