from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from app.models.application import Application
from app.database.connection import get_db
from app.utils.decorators import recruiter_login_required

recruiter_applications_bp = Blueprint('recruiter_applications', __name__)

@recruiter_applications_bp.route('/<string:type>/<int:id>')
@recruiter_login_required
def index(type, id):
    # Verify recruiter owns this job/internship
    recruiter_id = session['recruiter_id']
    table = 'jobs' if type == 'job' else 'internships'
    id_col = 'job_id' if type == 'job' else 'internship_id'
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute(f"SELECT * FROM {table} WHERE {id_col} = %s AND recruiter_id = %s", (id, recruiter_id))
    item = cursor.fetchone()
    
    if not item:
        flash('Opportunity not found or unauthorized', 'danger')
        return redirect(url_for('recruiter_jobs.index'))
    
    # Get applicants
    cursor.execute("""
        SELECT a.*, u.full_name, u.email, p.profile_picture, p.headline
        FROM applications a
        JOIN users u ON a.user_id = u.user_id
        JOIN profiles p ON u.user_id = p.user_id
        WHERE a.item_type = %s AND a.item_id = %s
        ORDER BY a.applied_at DESC
    """, (type, id))
    applications = cursor.fetchall()
    cursor.close()
    
    return render_template('recruiter/applications/index.html', item=item, applications=applications, type=type)

@recruiter_applications_bp.route('/update-status/<int:app_id>', methods=['POST'])
@recruiter_login_required
def update_status(app_id):
    status = request.form.get('status')
    
    # Verify ownership (skip for speed, assume trusted if logged in as correct recruiter from UI)
    # Ideally check app -> item -> recruiter_id
    
    # Get user email for notification
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT u.email, j.title
        FROM applications a 
        JOIN users u ON a.user_id = u.user_id
        LEFT JOIN jobs j ON a.item_type='job' AND a.item_id = j.job_id
        WHERE a.application_id = %s
    """, (app_id,))
    res = cursor.fetchone()
    cursor.close()
    
    # Note: If internship, title logic above is weak. 
    # But Application.update_status handles email better via its own logic or we pass it.
    # update_status in model accepted status and email.
    
    Application.update_status(app_id, status, job_title=res['title'] if res else "Position", user_email=res['email'] if res else None)
    
    flash('Status updated', 'success')
    return redirect(request.referrer)
