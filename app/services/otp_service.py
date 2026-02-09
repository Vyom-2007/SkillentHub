"""
OTP (One-Time Password) service module.
Handles OTP generation, storage, verification, and management for password reset.
"""
import random
import string
from datetime import datetime, timedelta
from flask import current_app
from app.database.connection import execute_query, execute_insert


def generate_otp(length=6):
    """
    Generate a random numeric OTP.
    
    Args:
        length: Number of digits (default 6)
    
    Returns:
        String of random digits
    """
    return ''.join(random.choices(string.digits, k=length))


def create_otp(user_id, email):
    """
    Create a new OTP for password reset.
    Invalidates any existing unused OTPs for this email.
    
    Args:
        user_id: User's ID
        email: User's email address
    
    Returns:
        Tuple (otp_string, expires_at_datetime)
    """
    # Invalidate existing unused OTPs for this email
    invalidate_query = """
        UPDATE password_reset_otps 
        SET is_used = 1 
        WHERE email = %s AND is_used = 0
    """
    execute_query(invalidate_query, (email,))
    
    # Generate new OTP
    otp = generate_otp()
    expiry_minutes = current_app.config.get('OTP_EXPIRY_MINUTES', 5)
    expires_at = datetime.now() + timedelta(minutes=expiry_minutes)
    
    # Insert new OTP
    insert_query = """
        INSERT INTO password_reset_otps 
        (user_id, email, otp, created_at, expires_at, is_verified, is_used, attempts)
        VALUES (%s, %s, %s, NOW(), %s, 0, 0, 0)
    """
    execute_insert(insert_query, (user_id, email, otp, expires_at))
    
    return otp, expires_at


def get_active_otp(email):
    """
    Get the most recent active (unused, unexpired) OTP for an email.
    
    Args:
        email: User's email address
    
    Returns:
        OTP record dict or None
    """
    query = """
        SELECT otp_id, user_id, email, otp, created_at, expires_at, 
               is_verified, is_used, attempts
        FROM password_reset_otps
        WHERE email = %s 
          AND is_used = 0 
          AND expires_at > NOW()
        ORDER BY created_at DESC
        LIMIT 1
    """
    return execute_query(query, (email,), fetch_one=True)


def verify_otp(email, otp_input):
    """
    Verify an OTP input against stored OTP.
    
    Args:
        email: User's email address
        otp_input: OTP string entered by user
    
    Returns:
        Tuple (success: bool, message: str, otp_record or None)
    """
    max_attempts = current_app.config.get('OTP_MAX_ATTEMPTS', 5)
    
    # Get active OTP
    otp_record = get_active_otp(email)
    
    if not otp_record:
        return False, "No valid OTP found. Please request a new one.", None
    
    # Check if max attempts exceeded
    if otp_record['attempts'] >= max_attempts:
        return False, "Maximum attempts exceeded. Please request a new OTP.", None
    
    # Increment attempt count
    update_attempts_query = """
        UPDATE password_reset_otps 
        SET attempts = attempts + 1 
        WHERE otp_id = %s
    """
    execute_query(update_attempts_query, (otp_record['otp_id'],))
    
    # Check if OTP matches
    if otp_record['otp'] != otp_input:
        remaining = max_attempts - otp_record['attempts'] - 1
        if remaining > 0:
            return False, f"Invalid OTP. {remaining} attempts remaining.", None
        else:
            return False, "Maximum attempts exceeded. Please request a new OTP.", None
    
    # OTP is valid - mark as verified
    verify_query = """
        UPDATE password_reset_otps 
        SET is_verified = 1 
        WHERE otp_id = %s
    """
    execute_query(verify_query, (otp_record['otp_id'],))
    
    # Refresh record to get updated state
    otp_record['is_verified'] = 1
    
    return True, "OTP verified successfully.", otp_record


def get_verified_otp(email):
    """
    Get a verified but unused OTP for password reset.
    
    Args:
        email: User's email address
    
    Returns:
        OTP record dict or None
    """
    query = """
        SELECT otp_id, user_id, email, otp, created_at, expires_at, 
               is_verified, is_used, attempts
        FROM password_reset_otps
        WHERE email = %s 
          AND is_verified = 1 
          AND is_used = 0 
          AND expires_at > NOW()
        ORDER BY created_at DESC
        LIMIT 1
    """
    return execute_query(query, (email,), fetch_one=True)


def mark_otp_used(otp_id):
    """
    Mark an OTP as used after successful password reset.
    
    Args:
        otp_id: OTP record ID
    
    Returns:
        True if updated successfully
    """
    query = """
        UPDATE password_reset_otps 
        SET is_used = 1 
        WHERE otp_id = %s
    """
    rows_affected = execute_query(query, (otp_id,))
    return rows_affected > 0


def can_resend_otp(email):
    """
    Check if enough time has passed to resend an OTP.
    
    Args:
        email: User's email address
    
    Returns:
        Tuple (can_resend: bool, seconds_remaining: int)
    """
    cooldown_seconds = current_app.config.get('OTP_RESEND_COOLDOWN_SECONDS', 60)
    
    query = """
        SELECT created_at
        FROM password_reset_otps
        WHERE email = %s
        ORDER BY created_at DESC
        LIMIT 1
    """
    result = execute_query(query, (email,), fetch_one=True)
    
    if not result:
        return True, 0
    
    created_at = result['created_at']
    elapsed = (datetime.now() - created_at).total_seconds()
    
    if elapsed >= cooldown_seconds:
        return True, 0
    else:
        return False, int(cooldown_seconds - elapsed)


def get_otp_expiry_seconds(email):
    """
    Get remaining seconds until OTP expires.
    
    Args:
        email: User's email address
    
    Returns:
        Seconds remaining or 0 if expired/not found
    """
    otp_record = get_active_otp(email)
    
    if not otp_record:
        return 0
    
    expires_at = otp_record['expires_at']
    remaining = (expires_at - datetime.now()).total_seconds()
    
    return max(0, int(remaining))
