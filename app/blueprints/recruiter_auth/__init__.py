from flask import Blueprint

recruiter_auth_bp = Blueprint('recruiter_auth', __name__)

from . import routes
