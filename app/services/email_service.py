from flask_mail import Message
from app import mail


def send_otp_email(recipient_email, otp_code):
    """
    Send a password-reset OTP email via Flask-Mail (Gmail SMTP).
    Returns True on success, error string on failure.
    """
    try:
        msg = Message(
            subject='SkillentHub — Your Password Reset OTP',
            recipients=[recipient_email],
        )
        msg.html = f"""
        <div style="font-family:'Segoe UI',Arial,sans-serif;max-width:480px;margin:auto;
                    padding:32px;background:#ffffff;border-radius:12px;
                    border:1px solid #e0e0e0;">
            <h2 style="color:#4f46e5;margin-bottom:8px;">SkillentHub</h2>
            <p style="color:#333;">You requested a password reset. Use the OTP below to verify your identity:</p>
            <div style="text-align:center;margin:24px 0;">
                <span style="display:inline-block;font-size:32px;font-weight:700;
                             letter-spacing:8px;padding:16px 32px;background:#f0f0ff;
                             border-radius:8px;color:#4f46e5;">{otp_code}</span>
            </div>
            <p style="color:#666;font-size:14px;">This code expires in <strong>5 minutes</strong>.</p>
            <p style="color:#999;font-size:12px;">If you didn't request this, you can safely ignore this email.</p>
        </div>
        """
        mail.send(msg)
        return True
    except Exception as e:
        return str(e)
