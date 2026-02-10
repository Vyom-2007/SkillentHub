import os
from flask import Flask, send_from_directory
from flask_session import Session
from flask_mail import Mail

# Global extensions (initialised in create_app)
sess = Session()
mail = Mail()


def create_app():
    app = Flask(__name__)

    # ── Load config ─────────────────────────────────────────
    app.config.from_object('config.Config')

    # Ensure session directory exists
    os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)

    # Ensure upload directories exist
    uploads_root = os.path.join(app.root_path, '..', 'uploads')
    os.makedirs(os.path.join(uploads_root, 'profiles'), exist_ok=True)
    os.makedirs(os.path.join(uploads_root, 'resumes'), exist_ok=True)

    # ── Initialise extensions ───────────────────────────────
    sess.init_app(app)
    mail.init_app(app)

    # ── Serve uploaded files ────────────────────────────────
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(
            os.path.join(app.root_path, '..', 'uploads'), filename
        )

    # ── Register blueprints ─────────────────────────────────
    from app.blueprints.auth import auth_bp
    app.register_blueprint(auth_bp)

    from app.blueprints.pages import pages_bp
    app.register_blueprint(pages_bp)

    from app.blueprints.profile import profile_bp
    app.register_blueprint(profile_bp)

    return app
