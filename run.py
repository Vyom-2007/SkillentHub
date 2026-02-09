"""
Application entry point.
Run this file to start the Flask development server.
"""
import os
from app import create_app

# Get environment from env var, default to development
env = os.getenv('FLASK_ENV', 'development')
app = create_app(env)

if __name__ == '__main__':
    # Ensure required directories exist
    os.makedirs('instance/sessions', exist_ok=True)
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Run the application
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('FLASK_PORT', 5000)),
        debug=app.config.get('DEBUG', True)
    )
