from flask import Blueprint

pages_bp = Blueprint(
    'pages',
    __name__,
    template_folder='../../templates',
)

from app.blueprints.pages import routes   # noqa: E402, F401
