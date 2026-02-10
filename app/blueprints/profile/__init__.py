from flask import Blueprint

profile_bp = Blueprint(
    'profile',
    __name__,
    url_prefix='/api/profile',
    template_folder='../../templates',
)

from app.blueprints.profile import routes   # noqa: E402, F401
