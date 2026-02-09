"""
Email service module.
Handles sending emails using Flask-Mail.
"""
from flask import current_app, render_template_string
from flask_mail import Message
from app import mail


def send_email(to, subject, html_body, text_body=None):
    """
    Send an email using Flask-Mail.
    
    Args:
        to: Recipient email address
        subject: Email subject
        html_body: HTML content of the email
        text_body: Plain text content (optional)
    
    Returns:
        True if sent successfully, False otherwise
    """
    try:
        msg = Message(
            subject=subject,
            recipients=[to],
            html=html_body,
            body=text_body or html_body
        )
        
        # If mail is suppressed (dev mode), log to console
        if current_app.config.get('MAIL_SUPPRESS_SEND'):
            current_app.logger.info(f"[EMAIL SUPPRESSED] To: {to}")
            current_app.logger.info(f"[EMAIL SUPPRESSED] Subject: {subject}")
            current_app.logger.info(f"[EMAIL SUPPRESSED] Body: {text_body or html_body}")
            print(f"\n{'='*50}")
            print(f"EMAIL TO: {to}")
            print(f"SUBJECT: {subject}")
            print(f"BODY:\n{text_body or 'See HTML'}")
            print(f"{'='*50}\n")
            return True
        
        mail.send(msg)
        return True
        
    except Exception as e:
        current_app.logger.error(f"Failed to send email: {e}")
        return False


def send_otp_email(email, otp, expires_in_minutes=5):
    """
    Send an OTP email for password reset.
    
    Args:
        email: Recipient email address
        otp: The OTP code
        expires_in_minutes: OTP validity period
    
    Returns:
        True if sent successfully, False otherwise
    """
    subject = "SkillentHub - Password Reset OTP"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Inter', Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #ffffff; padding: 30px; border: 1px solid #e2e8f0; border-top: none; }}
            .otp-code {{ font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #667eea; background: #f8fafc; padding: 20px; text-align: center; border-radius: 8px; margin: 20px 0; }}
            .footer {{ text-align: center; color: #64748b; font-size: 14px; padding: 20px; }}
            .warning {{ background: #fef3c7; color: #92400e; padding: 15px; border-radius: 8px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin: 0;">🔐 Password Reset</h1>
            </div>
            <div class="content">
                <p>Hello,</p>
                <p>You requested to reset your password for your SkillentHub account. Use the OTP below to verify your identity:</p>
                
                <div class="otp-code">{otp}</div>
                
                <p>This code will expire in <strong>{expires_in_minutes} minutes</strong>.</p>
                
                <div class="warning">
                    ⚠️ If you didn't request this password reset, please ignore this email. Your account is safe.
                </div>
            </div>
            <div class="footer">
                <p>© 2026 SkillentHub. All rights reserved.</p>
                <p>This is an automated message. Please do not reply.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_body = f"""
    SkillentHub - Password Reset OTP
    
    You requested to reset your password.
    
    Your OTP code is: {otp}
    
    This code will expire in {expires_in_minutes} minutes.
    
    If you didn't request this, please ignore this email.
    
    © 2026 SkillentHub
    """
    
    return send_email(email, subject, html_body, text_body)


def send_welcome_email(email, full_name):
    """
    Send a welcome email after registration.
    
    Args:
        email: User's email address
        full_name: User's full name
    
    Returns:
        True if sent successfully, False otherwise
    """
    subject = "Welcome to SkillentHub! 🎉"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Inter', Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #ffffff; padding: 30px; border: 1px solid #e2e8f0; border-top: none; }}
            .btn {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 30px; text-decoration: none; border-radius: 8px; font-weight: 600; }}
            .footer {{ text-align: center; color: #64748b; font-size: 14px; padding: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin: 0;">Welcome to SkillentHub! 🎉</h1>
            </div>
            <div class="content">
                <p>Hello {full_name},</p>
                <p>Thank you for joining SkillentHub! We're excited to have you as part of our community.</p>
                <p>Start exploring opportunities, connect with professionals, and take your career to the next level.</p>
                <p style="text-align: center; margin: 30px 0;">
                    <a href="#" class="btn">Get Started</a>
                </p>
            </div>
            <div class="footer">
                <p>© 2026 SkillentHub. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_body = f"""
    Welcome to SkillentHub!
    
    Hello {full_name},
    
    Thank you for joining SkillentHub! We're excited to have you as part of our community.
    
    Start exploring opportunities, connect with professionals, and take your career to the next level.
    
    © 2026 SkillentHub
    """
    
    return send_email(email, subject, html_body, text_body)
