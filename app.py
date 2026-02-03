"""
SkillentHub - Main Flask Application
"""

from flask import Flask, redirect, url_for
from config import Config


def create_app(config_class=Config):
    """Application factory function."""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Ensure upload directories exist
    import os
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'profiles'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'resumes'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'posts'), exist_ok=True)
    
    # Register blueprints
    from auth.routes import auth_bp
    from profile.routes import profile_bp
    from dashboard.routes import dashboard_bp
    from posts.routes import posts_bp
    from feed.routes import feed_bp
    from connections.routes import connections_bp
    from chat.routes import chat_bp
    from notifications.routes import notifications_bp
    from opportunities.routes import opportunities_bp
    from events.routes import events_bp
    from admin.routes import admin_bp
    from pages.routes import pages_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(posts_bp)
    app.register_blueprint(feed_bp)
    app.register_blueprint(connections_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(opportunities_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(pages_bp)  # Root routes (/, /about, /contact)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden_error(error):
        from flask import render_template
        return render_template('errors/403.html'), 403
    
    return app


# Create app instance
app = create_app()


if __name__ == '__main__':
    app.run(debug=True)
