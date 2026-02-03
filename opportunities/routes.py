"""
Opportunities routes blueprint for viewing and applying to job opportunities.
"""

import os
import time
from functools import wraps

from flask import Blueprint, render_template, redirect, url_for, flash, session, request, current_app
from werkzeug.utils import secure_filename
from database.db import execute_query
from opportunities.forms import ApplicationForm


# Create the opportunities blueprint
opportunities_bp = Blueprint('opportunities', __name__, url_prefix='/opportunities')


def login_required(f):
    """Decorator to require user login for protected routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@opportunities_bp.route('/')
def list_opportunities():
    """
    Display all job opportunities.
    Ordered by created_at DESC (newest first).
    """
    opportunities = execute_query(
        """
        SELECT id, title, company, location, job_type, salary_range, 
               description, requirements, created_at 
        FROM opportunities 
        ORDER BY created_at DESC
        """,
        fetch_all=True
    )
    
    return render_template('opportunities/list.html', opportunities=opportunities or [])


@opportunities_bp.route('/view/<int:id>')
def view_opportunity(id):
    """
    Display details of a specific opportunity.
    Also checks if the current user has already applied.
    """
    # Fetch opportunity details
    opportunity = execute_query(
        """
        SELECT id, title, company, location, job_type, salary_range, 
               description, requirements, created_at 
        FROM opportunities 
        WHERE id = %s
        """,
        (id,),
        fetch_one=True
    )
    
    if not opportunity:
        flash('Opportunity not found.', 'danger')
        return redirect(url_for('opportunities.list_opportunities'))
    
    # Check if user has already applied (if logged in)
    has_applied = False
    application = None
    if 'user_id' in session:
        application = execute_query(
            "SELECT * FROM applications WHERE user_id = %s AND opportunity_id = %s",
            (session['user_id'], id),
            fetch_one=True
        )
        has_applied = application is not None
    
    # Count total applications for this opportunity
    app_count = execute_query(
        "SELECT COUNT(*) as count FROM applications WHERE opportunity_id = %s",
        (id,),
        fetch_one=True
    )
    
    form = ApplicationForm()
    
    return render_template(
        'opportunities/details.html', 
        opportunity=opportunity,
        has_applied=has_applied,
        application=application,
        application_count=app_count['count'] if app_count else 0,
        form=form
    )


@opportunities_bp.route('/apply/<int:id>', methods=['POST'])
@login_required
def apply(id):
    """
    Submit an application for an opportunity.
    """
    user_id = session['user_id']
    
    # Check if opportunity exists
    opportunity = execute_query(
        "SELECT id, title FROM opportunities WHERE id = %s",
        (id,),
        fetch_one=True
    )
    
    if not opportunity:
        flash('Opportunity not found.', 'danger')
        return redirect(url_for('opportunities.list_opportunities'))
    
    # Check if user has already applied
    existing = execute_query(
        "SELECT id FROM applications WHERE user_id = %s AND opportunity_id = %s",
        (user_id, id),
        fetch_one=True
    )
    
    if existing:
        flash('You have already applied to this opportunity.', 'warning')
        return redirect(url_for('opportunities.view_opportunity', id=id))
    
    form = ApplicationForm()
    
    if form.validate_on_submit():
        resume = form.resume.data
        
        # Generate unique filename
        original_filename = secure_filename(resume.filename)
        timestamp = int(time.time())
        filename = f"app_{user_id}_{id}_{timestamp}.pdf"
        
        # Save resume file
        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'resumes')
        os.makedirs(upload_folder, exist_ok=True)
        resume_path = os.path.join(upload_folder, filename)
        resume.save(resume_path)
        
        # Insert application into database
        result = execute_query(
            """
            INSERT INTO applications (user_id, opportunity_id, resume_file, status, applied_at) 
            VALUES (%s, %s, %s, 'pending', NOW())
            """,
            (user_id, id, filename),
            commit=True
        )
        
        if result is not None:
            flash(f'Application submitted successfully for "{opportunity["title"]}"!', 'success')
            
            # Create notification for admin (optional)
            try:
                from notifications.utils import create_notification
                # Notify the user about their application
                create_notification(
                    user_id=user_id,
                    message=f'Your application for "{opportunity["title"]}" has been submitted.',
                    notification_type='opportunity'
                )
            except Exception:
                pass  # Notification is optional
        else:
            flash('Failed to submit application. Please try again.', 'danger')
            # Clean up uploaded file on failure
            if os.path.exists(resume_path):
                os.remove(resume_path)
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{error}', 'danger')
    
    return redirect(url_for('opportunities.view_opportunity', id=id))


@opportunities_bp.route('/my-applications')
@login_required
def my_applications():
    """
    View all applications submitted by the current user.
    """
    user_id = session['user_id']
    
    applications = execute_query(
        """
        SELECT a.id, a.status, a.resume_file, a.applied_at as created_at,
               o.id as opportunity_id, o.title, o.company, o.location
        FROM applications a
        INNER JOIN opportunities o ON a.opportunity_id = o.id
        WHERE a.user_id = %s
        ORDER BY a.applied_at DESC
        """,
        (user_id,),
        fetch_all=True
    )
    
    return render_template('opportunities/my_applications.html', applications=applications or [])


@opportunities_bp.route('/withdraw/<int:application_id>', methods=['POST'])
@login_required
def withdraw_application(application_id):
    """
    Withdraw an application (only if status is still pending).
    """
    user_id = session['user_id']
    
    # Fetch the application
    application = execute_query(
        "SELECT * FROM applications WHERE id = %s AND user_id = %s",
        (application_id, user_id),
        fetch_one=True
    )
    
    if not application:
        flash('Application not found.', 'danger')
        return redirect(url_for('opportunities.my_applications'))
    
    if application['status'] != 'pending':
        flash('Only pending applications can be withdrawn.', 'warning')
        return redirect(url_for('opportunities.my_applications'))
    
    # Delete the resume file
    if application['resume_file']:
        resume_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'resumes', application['resume_file'])
        if os.path.exists(resume_path):
            os.remove(resume_path)
    
    # Delete the application
    execute_query(
        "DELETE FROM applications WHERE id = %s AND user_id = %s",
        (application_id, user_id),
        commit=True
    )
    
    flash('Application withdrawn.', 'info')
    return redirect(url_for('opportunities.my_applications'))
