from flask import Blueprint

# Initialize blueprints to avoid 'ImportError' in __init__.py until properly implemented
profile_bp = Blueprint('profile', __name__)
network_bp = Blueprint('network', __name__)
connections_bp = Blueprint('connections', __name__)
posts_bp = Blueprint('posts', __name__)
messages_bp = Blueprint('messages', __name__)
notifications_bp = Blueprint('notifications', __name__)
teams_bp = Blueprint('teams', __name__)
opportunities_bp = Blueprint('opportunities', __name__)
settings_bp = Blueprint('settings', __name__)
pages_bp = Blueprint('pages', __name__)
