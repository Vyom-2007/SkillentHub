from flask import Flask
from flask_session import Session
from flask_mail import Mail
from config import Config
import os

# Initialize extensions
sess = Session()
mail = Mail()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions with app
    sess.init_app(app)
    mail.init_app(app)
    
    # Ensure upload directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'profiles'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'posts'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'resumes'), exist_ok=True)
    
    # Register Blueprints (Importing locally to avoid circular imports)
    from app.blueprints.auth.routes import auth_bp
    from app.blueprints.profile.routes import profile_bp
    from app.blueprints.network.routes import network_bp
    from app.blueprints.connections.routes import connections_bp
    from app.blueprints.posts.routes import posts_bp
    from app.blueprints.messages.routes import messages_bp
    from app.blueprints.notifications.routes import notifications_bp
    from app.blueprints.teams.routes import teams_bp
    from app.blueprints.opportunities.routes import opportunities_bp
    from app.blueprints.settings.routes import settings_bp
    from app.blueprints.pages.routes import pages_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(network_bp)
    app.register_blueprint(connections_bp)
    app.register_blueprint(posts_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(teams_bp)
    app.register_blueprint(opportunities_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(pages_bp)
    
    return app
