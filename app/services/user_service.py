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


def save_opportunity(user_id, item_type, item_id):
    """Save an opportunity (bookmark)."""
    query = """
        INSERT IGNORE INTO saved_jobs (user_id, item_type, item_id)
        VALUES (%s, %s, %s)
    """
    execute_update(query, (user_id, item_type, item_id))
    return True


def unsave_opportunity(user_id, item_type, item_id):
    """Unsave an opportunity."""
    query = """
        DELETE FROM saved_jobs 
        WHERE user_id = %s AND item_type = %s AND item_id = %s
    """
    execute_update(query, (user_id, item_type, item_id))
    return True


def get_saved_opportunities(user_id):
    """Get all saved opportunities for a user."""
    # We need to join with respective tables to get details.
    # Using UNION approach similar to recruiter dashboard or separate queries.
    # Given the complexity of joins, let's fetch basic info and then enrich or use a complex query.
    
    query = """
        SELECT s.save_id, s.item_type, s.item_id, s.saved_at,
               COALESCE(j.title, i.title, c.title, h.title) as title,
               COALESCE(r1.company_name, r2.company_name, r3.company_name, r4.company_name) as company_name,
               COALESCE(j.location, i.location, h.venue, 'Online') as location
        FROM saved_jobs s
        LEFT JOIN jobs j ON s.item_type = 'job' AND s.item_id = j.job_id
        LEFT JOIN internships i ON s.item_type = 'internship' AND s.item_id = i.internship_id
        LEFT JOIN competitions c ON s.item_type = 'competition' AND s.item_id = c.competition_id
        LEFT JOIN hackathons h ON s.item_type = 'hackathon' AND s.item_id = h.hackathon_id
        
        LEFT JOIN recruiters r1 ON j.recruiter_id = r1.recruiter_id
        LEFT JOIN recruiters r2 ON i.recruiter_id = r2.recruiter_id
        LEFT JOIN recruiters r3 ON c.recruiter_id = r3.recruiter_id
        LEFT JOIN recruiters r4 ON h.recruiter_id = r4.recruiter_id
        
        WHERE s.user_id = %s
        ORDER BY s.saved_at DESC
    """
    return execute_query(query, (user_id,), fetch_all=True) or []


def is_saved(user_id, item_type, item_id):
    """Check if an item is saved by the user."""
    query = "SELECT 1 FROM saved_jobs WHERE user_id = %s AND item_type = %s AND item_id = %s"
    result = execute_query(query, (user_id, item_type, item_id), fetch_one=True)
    return bool(result)


def get_saved_ids(user_id):
    """Get set of (item_type, item_id) for all saved items."""
    query = "SELECT item_type, item_id FROM saved_jobs WHERE user_id = %s"
    results = execute_query(query, (user_id,), fetch_all=True) or []
    return {(r['item_type'], r['item_id']) for r in results}
