"""
Admin panel routes blueprint for managing the application.
"""

from functools import wraps

from flask import Blueprint, render_template, redirect, url_for, flash, session, request, abort
from database.db import execute_query
from admin.forms import JobForm, EventForm


# Create the admin blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def login_required(f):
    """Decorator to require user login for protected routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin role for protected routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        
        if session.get('role') != 'admin':
            flash('Access denied. Admin privileges required.', 'danger')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/')
@admin_required
def dashboard():
    """
    Admin dashboard with platform statistics.
    """
    # Fetch total counts
    total_users = execute_query(
        "SELECT COUNT(*) as count FROM users",
        fetch_one=True
    )
    
    total_jobs = execute_query(
        "SELECT COUNT(*) as count FROM opportunities",
        fetch_one=True
    )
    
    total_applications = execute_query(
        "SELECT COUNT(*) as count FROM applications",
        fetch_one=True
    )
    
    total_events = execute_query(
        "SELECT COUNT(*) as count FROM events",
        fetch_one=True
    )
    
    total_event_registrations = execute_query(
        "SELECT COUNT(*) as count FROM event_registrations",
        fetch_one=True
    )
    
    total_posts = execute_query(
        "SELECT COUNT(*) as count FROM posts",
        fetch_one=True
    )
    
    total_connections = execute_query(
        "SELECT COUNT(*) as count FROM connections WHERE status = 'accepted'",
        fetch_one=True
    )
    
    # Recent applications
    recent_applications = execute_query(
        """
        SELECT a.id, a.status, a.created_at,
               u.full_name as applicant_name,
               o.title as job_title
        FROM applications a
        INNER JOIN users u ON a.user_id = u.id
        INNER JOIN opportunities o ON a.opportunity_id = o.id
        ORDER BY a.created_at DESC
        LIMIT 10
        """,
        fetch_all=True
    )
    
    # Recent users
    recent_users = execute_query(
        """
        SELECT id, full_name, email, role, created_at
        FROM users
        ORDER BY created_at DESC
        LIMIT 10
        """,
        fetch_all=True
    )
    
    return render_template(
        'admin/dashboard.html',
        total_users=total_users['count'] if total_users else 0,
        total_jobs=total_jobs['count'] if total_jobs else 0,
        total_applications=total_applications['count'] if total_applications else 0,
        total_events=total_events['count'] if total_events else 0,
        total_event_registrations=total_event_registrations['count'] if total_event_registrations else 0,
        total_posts=total_posts['count'] if total_posts else 0,
        total_connections=total_connections['count'] if total_connections else 0,
        recent_applications=recent_applications or [],
        recent_users=recent_users or []
    )


@admin_bp.route('/add-job', methods=['GET', 'POST'])
@admin_required
def add_job():
    """
    Add a new job opportunity.
    """
    form = JobForm()
    
    if form.validate_on_submit():
        result = execute_query(
            """
            INSERT INTO opportunities 
            (title, company, job_type, location, salary_range, description, requirements, created_at) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """,
            (
                form.title.data,
                form.company.data,
                form.job_type.data,
                form.location.data or None,
                form.salary_range.data or None,
                form.description.data,
                form.requirements.data or None
            ),
            commit=True
        )
        
        if result is not None:
            flash(f'Job "{form.title.data}" posted successfully!', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Failed to post job. Please try again.', 'danger')
    
    return render_template('admin/add_job.html', form=form)


@admin_bp.route('/add-event', methods=['GET', 'POST'])
@admin_required
def add_event():
    """
    Add a new event.
    """
    form = EventForm()
    
    if form.validate_on_submit():
        # Parse max participants
        max_participants = None
        if form.max_participants.data:
            try:
                max_participants = int(form.max_participants.data)
            except ValueError:
                flash('Max participants must be a number.', 'warning')
                return render_template('admin/add_event.html', form=form)
        
        result = execute_query(
            """
            INSERT INTO events 
            (title, type, event_date, location, max_participants, description, created_at) 
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """,
            (
                form.title.data,
                form.event_type.data,
                form.event_date.data,
                form.location.data or None,
                max_participants,
                form.description.data
            ),
            commit=True
        )
        
        if result is not None:
            flash(f'Event "{form.title.data}" created successfully!', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Failed to create event. Please try again.', 'danger')
    
    return render_template('admin/add_event.html', form=form)


@admin_bp.route('/jobs')
@admin_required
def list_jobs():
    """
    List all job opportunities.
    """
    jobs = execute_query(
        """
        SELECT o.*, 
               (SELECT COUNT(*) FROM applications WHERE opportunity_id = o.id) as application_count
        FROM opportunities o
        ORDER BY o.created_at DESC
        """,
        fetch_all=True
    )
    
    return render_template('admin/jobs.html', jobs=jobs or [])


@admin_bp.route('/events')
@admin_required
def list_events():
    """
    List all events.
    """
    events = execute_query(
        """
        SELECT e.*, 
               (SELECT COUNT(*) FROM event_registrations WHERE event_id = e.id) as registration_count
        FROM events e
        ORDER BY e.event_date DESC
        """,
        fetch_all=True
    )
    
    return render_template('admin/events.html', events=events or [])


@admin_bp.route('/users')
@admin_required
def list_users():
    """
    List all users.
    """
    users = execute_query(
        """
        SELECT id, full_name, email, role, created_at
        FROM users
        ORDER BY created_at DESC
        """,
        fetch_all=True
    )
    
    return render_template('admin/users.html', users=users or [])


@admin_bp.route('/delete-job/<int:job_id>', methods=['POST'])
@admin_required
def delete_job(job_id):
    """
    Delete a job opportunity.
    """
    # Delete related applications first
    execute_query(
        "DELETE FROM applications WHERE opportunity_id = %s",
        (job_id,),
        commit=True
    )
    
    # Delete the job
    execute_query(
        "DELETE FROM opportunities WHERE id = %s",
        (job_id,),
        commit=True
    )
    
    flash('Job deleted successfully.', 'info')
    return redirect(url_for('admin.list_jobs'))


@admin_bp.route('/delete-event/<int:event_id>', methods=['POST'])
@admin_required
def delete_event(event_id):
    """
    Delete an event.
    """
    # Delete related registrations first
    execute_query(
        "DELETE FROM event_registrations WHERE event_id = %s",
        (event_id,),
        commit=True
    )
    
    # Delete the event
    execute_query(
        "DELETE FROM events WHERE id = %s",
        (event_id,),
        commit=True
    )
    
    flash('Event deleted successfully.', 'info')
    return redirect(url_for('admin.list_events'))
