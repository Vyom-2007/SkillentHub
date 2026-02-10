from flask import Blueprint

recruiter_jobs_bp = Blueprint('recruiter_jobs', __name__)

from . import routes
