"""
Flask application factory.
Creates and configures the Flask application instance.
"""
from flask import Flask
from flask_session import Session
from flask_mail import Mail
import os

# Initialize extensions
session = Session()
mail = Mail()


def create_app(config_name='development'):
    """
    Application factory function.
    
    Args:
        config_name: Configuration environment name ('development', 'production', 'testing')
    
    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    from config import config
    app.config.from_object(config.get(config_name, config['default']))
    
    # Ensure session directory exists
    session_dir = app.config.get('SESSION_FILE_DIR')
    if session_dir:
        os.makedirs(session_dir, exist_ok=True)
    
    # Initialize extensions with app
    session.init_app(app)
    mail.init_app(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    return app


def register_blueprints(app):
    """Register all application blueprints."""
    
    # Auth blueprint (user authentication)
    from app.blueprints.auth.routes import auth_bp
    app.register_blueprint(auth_bp)
    
    # Profile blueprint (user profiles)
    from app.blueprints.profile.routes import profile_bp
    app.register_blueprint(profile_bp)
    
    # Posts blueprint (feed and posts)
    from app.blueprints.posts.routes import posts_bp
    app.register_blueprint(posts_bp)
    
    # Network blueprint (user directory)
    from app.blueprints.network.routes import network_bp
    app.register_blueprint(network_bp)
    
    # Messages blueprint (direct messaging)
    from app.blueprints.messages.routes import messages_bp
    app.register_blueprint(messages_bp)
    
    # Opportunities blueprint (jobs & internships)
    from app.blueprints.opportunities.routes import opportunities_bp
    app.register_blueprint(opportunities_bp)
    
    # Applications blueprint (apply & track)
    from app.blueprints.applications.routes import applications_bp
    app.register_blueprint(applications_bp)
    
    # Competitions blueprint
    from app.blueprints.opportunities.competitions import competitions_bp
    app.register_blueprint(competitions_bp)
    
    # Hackathons blueprint
    from app.blueprints.opportunities.hackathons import hackathons_bp
    app.register_blueprint(hackathons_bp)
    
    # Notifications blueprint
    from app.blueprints.notifications.routes import notifications_bp
    app.register_blueprint(notifications_bp)
    
    # Settings blueprint
    from app.blueprints.settings.routes import settings_bp
    app.register_blueprint(settings_bp)

    # Connections blueprint
    from app.blueprints.connections.routes import connections_bp
    app.register_blueprint(connections_bp)

    # Teams blueprint
    from app.blueprints.teams.routes import teams_bp
    app.register_blueprint(teams_bp)


def register_error_handlers(app):
    """Register error handlers for the application."""
    
    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        return render_template('errors/500.html'), 500
