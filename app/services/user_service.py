"""
User service.
Handles user account operations including password change and privacy settings.
"""
import bcrypt
from app.database.connection import execute_query, execute_update


def get_user_by_id(user_id):
    """Get user by ID."""
    query = "SELECT user_id, email, password_hash FROM users WHERE user_id = %s"
    return execute_query(query, (user_id,), fetch_one=True)


def verify_password(user_id, current_password):
    """Verify if the current password is correct."""
    user = get_user_by_id(user_id)
    if not user:
        return False
    
    stored_hash = user['password_hash']
    if isinstance(stored_hash, str):
        stored_hash = stored_hash.encode('utf-8')
    
    return bcrypt.checkpw(current_password.encode('utf-8'), stored_hash)


def update_password(user_id, new_password):
    """Update user's password."""
    # Hash the new password
    password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
    
    query = "UPDATE users SET password_hash = %s WHERE user_id = %s"
    return execute_update(query, (password_hash.decode('utf-8'), user_id))


def get_privacy_settings(user_id):
    """Get user's privacy settings."""
    query = """
        SELECT visibility, show_email, show_phone
        FROM profiles
        WHERE user_id = %s
    """
    result = execute_query(query, (user_id,), fetch_one=True)
    if result:
        return {
            'visibility': result['visibility'] or 'public',
            'show_email': bool(result.get('show_email', 1)),
            'show_phone': bool(result.get('show_phone', 0))
        }
    return {
        'visibility': 'public',
        'show_email': True,
        'show_phone': False
    }


def update_privacy_settings(user_id, visibility, show_email, show_phone):
    """Update user's privacy settings."""
    query = """
        UPDATE profiles 
        SET visibility = %s, show_email = %s, show_phone = %s
        WHERE user_id = %s
    """
    return execute_update(query, (visibility, int(show_email), int(show_phone), user_id))


def validate_password_complexity(password):
    """Validate password meets complexity requirements."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    return True, None
