"""
Email Service.
Handles sending emails using Flask-Mail.
"""
from flask_mail import Message
from flask import current_app, render_template_string

def send_otp_email(to_email, user_name, otp):
    """
    Send Password Reset OTP email.
    """
    # Import mail here to avoid circular dependency
    from app import mail
    subject = "[SkillentHub] Password Reset OTP"
    
    body_template = """
Hi {{ user_name }},

You requested to reset your password. Your One-Time Password (OTP) is:

{{ otp }}

This OTP is valid for 5 minutes only.

If you didn't request this, please ignore this email and your password will remain unchanged.

Never share this OTP with anyone.

Thanks,
SkillentHub Team
    """
    
    body = render_template_string(body_template, user_name=user_name, otp=otp)
    
    try:
        msg = Message(
            subject=subject,
            recipients=[to_email],
            body=body,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER')
        )
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send email to {to_email}: {e}")
        return False


def send_status_update_email(to_email, candidate_name, item_title, company_name, status, application_id):
    """
    Send Application Status Update email (Shortlisted/Accepted).
    """
    # Import mail here to avoid circular dependency
    from app import mail
    
    if status == 'shortlisted':
        subject = f"[SkillentHub] Application Update - {item_title}"
        body_template = """
Hi {{ candidate_name }},

Great news! Your application for the position of "{{ item_title }}" at {{ company_name }} has been SHORTLISTED.

This means you've been selected for the next round of the hiring process.

Login to your SkillentHub account to view complete details:
https://skillenthub.com/applications/{{ application_id }}

Best of luck for the next steps!

Thanks,
SkillentHub Team
        """
    elif status == 'accepted':
        subject = f"[SkillentHub] Congratulations - Application Accepted for {item_title}"
        body_template = """
Hi {{ candidate_name }},

Congratulations! We're excited to inform you that your application for "{{ item_title }}" at {{ company_name }} has been ACCEPTED.

Login to your SkillentHub account for next steps:
https://skillenthub.com/applications/{{ application_id }}

Welcome aboard!

Thanks,
SkillentHub Team
        """
    elif status == 'rejected':
        subject = f"[SkillentHub] Update on your application for {item_title}"
        body_template = """
Hi {{ candidate_name }},

Thank you for your interest in the "{{ item_title }}" position at {{ company_name }}.

After careful consideration, we regret to inform you that we will not be moving forward with your application at this time.

We encourage you to apply for other opportunities on SkillentHub that match your skills.

We wish you the best in your job search.

Thanks,
SkillentHub Team
        """
    else:
        return False # No email for other statuses

    body = render_template_string(body_template, 
                                  candidate_name=candidate_name, 
                                  item_title=item_title,
                                  company_name=company_name,
                                  application_id=application_id)
    
    try:
        msg = Message(
            subject=subject,
            recipients=[to_email],
            body=body,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER')
        )
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send status email to {to_email}: {e}")
        return False


def send_welcome_email(to_email, user_name):
    """
    Send a welcome email after successful registration.
    """
    from app import mail
    subject = "[SkillentHub] Welcome to SkillentHub!"

    body_template = """
Hi {{ user_name }},

Welcome to SkillentHub! 🎉

Your account has been created successfully. Here's what you can do next:

• Complete your profile to stand out
• Browse jobs and internships
• Join hackathons and competitions
• Connect with peers and recruiters

Login to get started: https://skillenthub.com/login

Thanks,
SkillentHub Team
    """

    body = render_template_string(body_template, user_name=user_name)

    try:
        msg = Message(
            subject=subject,
            recipients=[to_email],
            body=body,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER')
        )
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send welcome email to {to_email}: {e}")
        return False
