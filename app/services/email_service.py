from flask_mail import Message
from flask import current_app
from app import mail

def send_otp_email(to_email, otp):
    msg = Message("Password Reset OTP - SkillentHub",
                  recipients=[to_email])
    msg.body = f"Your OTP for password reset is: {otp}. It expires in 5 minutes."
    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def send_application_status_email(to_email, status, job_title):
    msg = Message(f"Application Update: {status} - SkillentHub",
                  recipients=[to_email])
    msg.body = f"Your application for {job_title} has been updated to: {status}."
    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
