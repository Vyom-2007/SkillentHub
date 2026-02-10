from flask import Blueprint

recruiter_applications_bp = Blueprint('recruiter_applications', __name__)

from . import routes
