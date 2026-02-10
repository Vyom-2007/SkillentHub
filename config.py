"""
Flask application configuration.
Loads settings from environment variables with sensible defaults.
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration class."""
    
    # Flask core settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-super-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Database settings (MySQL with pymysql)
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'skillenthub')
    
    # Session settings
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'sessions')
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)  # 30-minute session timeout
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'skillenthub_'
    
    # Flask-Mail settings
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@skillenthub.com')
    MAIL_SUPPRESS_SEND = os.getenv('MAIL_SUPPRESS_SEND', 'False').lower() == 'true'
    
    # OTP settings
    OTP_EXPIRY_MINUTES = 5
    OTP_MAX_ATTEMPTS = 5
    OTP_RESEND_COOLDOWN_SECONDS = 60
    
    # Upload settings
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    # MAIL_SUPPRESS_SEND is now controlled by .env file


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DB_NAME = 'skillenthub_test'


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
