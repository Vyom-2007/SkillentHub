from flask import Blueprint

posts_bp = Blueprint(
    'posts',
    __name__,
    url_prefix='/api',
    template_folder='../../templates',
)

from app.blueprints.posts import routes   # noqa: E402, F401
