"""
OTP (One-Time Password) utilities for password reset functionality.
"""

import random
import string


def generate_otp():
    """
    Generate a 6-digit random OTP code.
    
    Returns:
        str: A 6-digit OTP code as a string.
    """
    return ''.join(random.choices(string.digits, k=6))


def send_otp_email(email, otp):
    """
    Simulate sending an OTP email to the user.
    
    In production, this should integrate with an SMTP server or
    email service provider (e.g., SendGrid, AWS SES).
    
    For now, this prints the OTP to the console for testing purposes.
    
    Args:
        email (str): The recipient's email address.
        otp (str): The OTP code to send.
    
    Returns:
        bool: True if the email was "sent" successfully.
    """
    print("=" * 50)
    print(f"[EMAIL SIMULATION] Sending OTP to: {email}")
    print(f"[EMAIL SIMULATION] Your OTP Code: {otp}")
    print(f"[EMAIL SIMULATION] This OTP expires in 10 minutes.")
    print("=" * 50)
    
    # In production, implement actual email sending here:
    # Example with Flask-Mail:
    # from flask_mail import Message
    # from flask import current_app
    # msg = Message(
    #     subject="Password Reset OTP",
    #     sender=current_app.config['MAIL_DEFAULT_SENDER'],
    #     recipients=[email]
    # )
    # msg.body = f"Your OTP code is: {otp}. It expires in 10 minutes."
    # mail.send(msg)
    
    return True
