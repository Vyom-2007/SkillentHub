
"""
Recruiter Authentication Service.
Handles recruiter registration, login verification, and password management.
"""
import bcrypt
from app.database.connection import execute_query, execute_insert, execute_update

def hash_password(password):
    """
    Hash a password using bcrypt.
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password, password_hash):
    """
    Verify a password against its hash.
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception:
        return False


def get_recruiter_by_email(email):
    """
    Retrieve a recruiter by their email address.
    """
    query = """
        SELECT recruiter_id, company_name, company_email, password_hash, 
               created_at, is_active
        FROM recruiters 
        WHERE company_email = %s
    """
    return execute_query(query, (email,), fetch_one=True)


def get_recruiter_by_id(recruiter_id):
    """
    Retrieve a recruiter by their ID.
    """
    query = """
        SELECT recruiter_id, company_name, company_email, password_hash, 
               created_at, is_active
        FROM recruiters 
        WHERE recruiter_id = %s
    """
    return execute_query(query, (recruiter_id,), fetch_one=True)


def email_exists(email):
    """
    Check if an email is already registered.
    """
    recruiter = get_recruiter_by_email(email)
    return recruiter is not None


def register_recruiter(company_name, email, password):
    """
    Register a new recruiter.
    Returns: Tuple (success: bool, result: recruiter_id or error_message)
    """
    # Check if email exists
    if email_exists(email):
        return False, "Email is already registered"
    
    password_hash = hash_password(password)
    
    query = """
        INSERT INTO recruiters (company_name, company_email, password_hash)
        VALUES (%s, %s, %s)
    """
    try:
        recruiter_id = execute_insert(query, (company_name, email, password_hash))
        
        # Send welcome email
        from app.services import email_service
        email_service.send_welcome_email(email, company_name)
        
        return True, recruiter_id
    except Exception as e:
        return False, str(e)


def verify_recruiter(email, password):
    """
    Verify recruiter credentials for login.
    Returns: Tuple (success: bool, result: recruiter_dict or error_message)
    """
    recruiter = get_recruiter_by_email(email)
    
    if not recruiter:
        return False, "Invalid email or password"
    
    if not recruiter.get('is_active', True):
        return False, "Account is deactivated. Contact support."
    
    if not verify_password(password, recruiter['password_hash']):
        return False, "Invalid email or password"
    
    return True, recruiter


def verify_recruiter_by_id(recruiter_id, password):
    """
    Verify recruiter credentials by ID (for settings/password change).
    Returns: Tuple (success: bool, result: recruiter_dict or error_message)
    """
    recruiter = get_recruiter_by_id(recruiter_id)
    if not recruiter:
        return False, "Recruiter not found"
        
    if not verify_password(password, recruiter['password_hash']):
        return False, "Invalid email or password"
    
    # Update last login timestamp
    execute_update("UPDATE recruiters SET last_login = NOW() WHERE recruiter_id = %s", (recruiter['recruiter_id'],))
    
    return True, recruiter


def update_password(recruiter_id, new_password):
    """
    Update a recruiter's password.
    """
    password_hash = hash_password(new_password)
    
    query = "UPDATE recruiters SET password_hash = %s WHERE recruiter_id = %s"
    rows_affected = execute_update(query, (password_hash, recruiter_id))
    return rows_affected > 0


def initiate_password_reset(email):
    """
    Initiate password reset process.
    """
    from app.services import otp_service, email_service
    from datetime import datetime
    
    # 1. Check Recruiter (using internal fetch to avoid circular deps if any)
    recruiter = get_recruiter_by_email(email)
    
    if not recruiter:
        return False, "Email not found."
    
    # 2. Check Cooldown
    can_resend, seconds_remaining = otp_service.can_resend_otp(email)
    if not can_resend:
        return False, f"Please wait {seconds_remaining} seconds before requesting a new OTP."
        
    # 3. Generate OTP
    otp, _ = otp_service.create_otp(
        user_id=None,
        email=email,
        recruiter_id=recruiter['recruiter_id']
    )
    
    # 4. Send Email
    if email_service.send_otp_email(email, recruiter['company_name'], otp):
        return True, "OTP sent to your email."
    else:
        return False, "Failed to send email. Please try again later."
