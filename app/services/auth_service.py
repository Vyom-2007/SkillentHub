"""
Authentication service module.
Handles user registration, login verification, and password management.
"""
import bcrypt
from app.database.connection import execute_query, execute_insert


def hash_password(password):
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password string
    
    Returns:
        Hashed password string
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password, password_hash):
    """
    Verify a password against its hash.
    
    Args:
        password: Plain text password to verify
        password_hash: Stored password hash
    
    Returns:
        True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception:
        return False


def get_user_by_email(email):
    """
    Retrieve a user by their email address.
    
    Args:
        email: User's email address
    
    Returns:
        User dict or None if not found
    """
    query = """
        SELECT user_id, email, password_hash, created_at, last_login, is_active
        FROM users
        WHERE email = %s
    """
    return execute_query(query, (email,), fetch_one=True)


def get_user_by_id(user_id):
    """
    Retrieve a user by their ID.
    
    Args:
        user_id: User's ID
    
    Returns:
        User dict or None if not found
    """
    query = """
        SELECT user_id, email, created_at, last_login, is_active
        FROM users
        WHERE user_id = %s
    """
    return execute_query(query, (user_id,), fetch_one=True)


def get_user_profile(user_id):
    """
    Retrieve user profile information.
    
    Args:
        user_id: User's ID
    
    Returns:
        Profile dict or None
    """
    query = """
        SELECT profile_id, user_id, full_name, headline, bio, 
               profile_picture, location, phone, updated_at
        FROM profiles
        WHERE user_id = %s
    """
    return execute_query(query, (user_id,), fetch_one=True)


def email_exists(email):
    """
    Check if an email is already registered.
    
    Args:
        email: Email address to check
    
    Returns:
        True if email exists, False otherwise
    """
    user = get_user_by_email(email)
    return user is not None


def register_user(email, password, full_name):
    """
    Register a new user.
    
    Args:
        email: User's email address
        password: Plain text password
        full_name: User's full name
    
    Returns:
        Tuple (success: bool, user_id or error_message)
    """
    # Check if email already exists
    if email_exists(email):
        return False, "Email is already registered"
    
    # Hash the password
    password_hash = hash_password(password)
    
    try:
        # Insert into users table
        user_query = """
            INSERT INTO users (email, password_hash, created_at, is_active)
            VALUES (%s, %s, NOW(), 1)
        """
        user_id = execute_insert(user_query, (email, password_hash))
        
        # Create profile entry
        profile_query = """
            INSERT INTO profiles (user_id, full_name)
            VALUES (%s, %s)
        """
        execute_insert(profile_query, (user_id, full_name))
        
        return True, user_id
        
    except Exception as e:
        return False, str(e)


def verify_user(email, password):
    """
    Verify user credentials for login.
    
    Args:
        email: User's email address
        password: Plain text password
    
    Returns:
        Tuple (success: bool, user_dict or error_message)
    """
    user = get_user_by_email(email)
    
    if not user:
        return False, "Invalid email or password"
    
    if not user.get('is_active'):
        return False, "Account is inactive"
    
    if not verify_password(password, user['password_hash']):
        return False, "Invalid email or password"
    
    # Update last login timestamp
    update_query = """
        UPDATE users SET last_login = NOW() WHERE user_id = %s
    """
    execute_query(update_query, (user['user_id'],))
    
    # Get profile for full name
    profile = get_user_profile(user['user_id'])
    
    return True, {
        'user_id': user['user_id'],
        'email': user['email'],
        'full_name': profile.get('full_name') if profile else None
    }


def update_password(user_id, new_password):
    """
    Update a user's password.
    
    Args:
        user_id: User's ID
        new_password: New plain text password
    
    Returns:
        True if updated successfully, False otherwise
    """
    password_hash = hash_password(new_password)
    
    query = """
        UPDATE users 
        SET password_hash = %s 
        WHERE user_id = %s
    """
    rows_affected = execute_query(query, (password_hash, user_id))
    return rows_affected > 0


def initiate_password_reset(email):
    """
    Initiate password reset process.
    Generates OTP, saves to DB, and sends email.
    
    Args:
        email: User's email address
    
    Returns:
        Tuple (success: bool, message: str)
    """
    import random
    from app.services import email_service
    
    # 1. Check User
    user = get_user_by_email(email)
    if not user:
        return False, "Email not found."
    
    user_id = user['user_id']
    
    # Get user name for email
    profile = get_user_profile(user_id)
    user_name = profile['full_name'] if profile else "User"
    
    # 2. Check Cooldown (60 seconds)
    cooldown_sql = """
        SELECT created_at FROM password_reset_otps 
        WHERE email = %s 
        ORDER BY created_at DESC LIMIT 1
    """
    last_otp = execute_query(cooldown_sql, (email,), fetch_one=True)
    
    if last_otp:
        # Check if created within last 60 seconds
        # Note: formatting might be needed depending on DB driver return type (often datetime)
        from datetime import datetime, timedelta
        
        time_diff = datetime.now() - last_otp['created_at']
        if time_diff.total_seconds() < 60:
            return False, "Please wait 60 seconds before resending."

    # 3. Generate OTP
    otp = str(random.randint(100000, 999999))
    
    # 4. Save to DB (Expiry +5 mins)
    insert_sql = """
        INSERT INTO password_reset_otps (user_id, email, otp, created_at, expires_at)
        VALUES (%s, %s, %s, NOW(), NOW() + INTERVAL 5 MINUTE)
    """
    execute_insert(insert_sql, (user_id, email, otp))
    
    # 5. Send Email
    if email_service.send_otp_email(email, user_name, otp):
        return True, "OTP sent to your email."
    else:
        return False, "Failed to send email. Please try again later."
