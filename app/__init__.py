import os
from flask import Flask
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

    # ── Initialise extensions ───────────────────────────────
    sess.init_app(app)
    mail.init_app(app)

    # ── Register blueprints ─────────────────────────────────
    from app.blueprints.auth import auth_bp
    app.register_blueprint(auth_bp)

    from app.blueprints.pages import pages_bp
    app.register_blueprint(pages_bp)

    return app
