from flask import Blueprint

competitions_bp = Blueprint('competitions', __name__)

from . import routes
