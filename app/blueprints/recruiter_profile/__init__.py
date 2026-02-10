from flask import Blueprint

recruiter_profile_bp = Blueprint('recruiter_profile', __name__)

from . import routes
