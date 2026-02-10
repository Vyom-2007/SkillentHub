from flask import Blueprint

recruiter_competitions_bp = Blueprint('recruiter_competitions', __name__)

from . import routes
