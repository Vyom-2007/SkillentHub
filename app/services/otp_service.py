import random
import string
from app.database.connection import get_db_connection


def generate_otp(user_id, email):
    """
    Invalidate any previous unused OTPs for this email,
    generate a new 6-digit OTP, insert it with a 5-minute expiry.
    Returns the OTP string.
    """
    otp_code = ''.join(random.choices(string.digits, k=6))

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Invalidate old OTPs
            cur.execute(
                "UPDATE password_reset_otps SET is_used = 1 "
                "WHERE email = %s AND is_used = 0",
                (email,),
            )
            # Insert new OTP (expires in 5 minutes)
            cur.execute(
                "INSERT INTO password_reset_otps "
                "(user_id, email, otp, expires_at) "
                "VALUES (%s, %s, %s, DATE_ADD(NOW(), INTERVAL 5 MINUTE))",
                (user_id, email, otp_code),
            )
    finally:
        conn.close()

    return otp_code


def verify_otp(email, otp_code):
    """
    Verify the latest OTP for the given email.
    Returns a dict:
      { 'success': True/False, 'message': str }

    Security:
    - Checks expiry
    - Increments attempts on failure
    - Locks OTP after 3 wrong attempts
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Get the latest unused OTP for this email
            cur.execute(
                "SELECT * FROM password_reset_otps "
                "WHERE email = %s AND is_used = 0 "
                "ORDER BY created_at DESC LIMIT 1",
                (email,),
            )
            record = cur.fetchone()

            if not record:
                return {'success': False, 'message': 'No OTP found. Please request a new one.'}

            # Check if locked (> 3 attempts)
            if record['attempts'] >= 3:
                return {'success': False, 'message': 'OTP locked due to too many failed attempts. Please request a new one.'}

            # Check expiry
            cur.execute("SELECT NOW() as now_ts")
            now = cur.fetchone()['now_ts']
            if now > record['expires_at']:
                return {'success': False, 'message': 'OTP has expired. Please request a new one.'}

            # Check OTP value
            if record['otp'] != otp_code:
                cur.execute(
                    "UPDATE password_reset_otps SET attempts = attempts + 1 WHERE otp_id = %s",
                    (record['otp_id'],),
                )
                remaining = 2 - record['attempts']  # after this increment
                if remaining <= 0:
                    return {'success': False, 'message': 'OTP locked due to too many failed attempts. Please request a new one.'}
                return {'success': False, 'message': f'Invalid OTP. {remaining} attempt(s) remaining.'}

            # OTP matches — mark as verified
            cur.execute(
                "UPDATE password_reset_otps SET is_verified = 1 WHERE otp_id = %s",
                (record['otp_id'],),
            )
            return {'success': True, 'message': 'OTP verified successfully.'}
    finally:
        conn.close()


def is_otp_verified(email):
    """Check if there is a verified, unused OTP for this email."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM password_reset_otps "
                "WHERE email = %s AND is_verified = 1 AND is_used = 0 "
                "ORDER BY created_at DESC LIMIT 1",
                (email,),
            )
            return cur.fetchone()
    finally:
        conn.close()


def mark_otp_used(otp_id):
    """Mark an OTP record as used after password reset."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE password_reset_otps SET is_used = 1 WHERE otp_id = %s",
                (otp_id,),
            )
    finally:
        conn.close()
