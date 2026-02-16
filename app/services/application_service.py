"""
Application service.
Handles job/internship applications, resume uploads, and tracking.
"""
import os
import uuid
from flask import current_app
from app.database.connection import execute_query, execute_insert, execute_update, get_db_connection


ALLOWED_EXTENSIONS = {'pdf'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def save_resume(file):
    """Save resume file and return filename."""
    if not file or not file.filename:
        return None, "No file provided"
    
    # Check extension
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_EXTENSIONS:
        return None, "Only PDF files are allowed"
    
    # Check file size
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    
    if size > MAX_FILE_SIZE:
        return None, "File size exceeds 10MB limit"
    
    # Generate unique filename
    filename = f"resume_{uuid.uuid4().hex[:12]}.pdf"
    
    # Create upload directory if needed
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'resumes')
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save file
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)
    
    return filename, None


def apply_to_opportunity(user_id, item_type, item_id, resume_file=None, cover_letter=None):
    """
    Apply to a job or internship.
    
    Args:
        user_id: Current user ID
        item_type: 'job' or 'internship'
        item_id: Job or internship ID
        resume_file: Uploaded resume file
        cover_letter: Cover letter text
    """
    # Check if already applied
    if has_applied(user_id, item_type, item_id):
        return False, "You have already applied to this opportunity"
    
    # Validate cover letter length
    if cover_letter:
        cover_letter = cover_letter.strip()[:5000]
    
    # Save resume if provided
    resume_path = None
    if resume_file and resume_file.filename:
        resume_path, error = save_resume(resume_file)
        if error:
            return False, error
    
    # Insert application
    query = """
        INSERT INTO applications (user_id, item_type, item_id, resume_path, cover_letter)
        VALUES (%s, %s, %s, %s, %s)
    """
    application_id = execute_insert(query, (user_id, item_type, item_id, resume_path, cover_letter))
    
    if application_id:
        return True, application_id
    return False, "Failed to submit application"


def has_applied(user_id, item_type, item_id):
    """Check if user has already applied to an opportunity."""
    query = """
        SELECT application_id FROM applications 
        WHERE user_id = %s AND item_type = %s AND item_id = %s
    """
    result = execute_query(query, (user_id, item_type, item_id), fetch_one=True)
    return result is not None


def get_user_applications(user_id, item_type=None, status=None, page=1, per_page=20):
    """Get all applications for a user with optional filters."""
    offset = (page - 1) * per_page
    params = [user_id]
    where_clauses = ["a.user_id = %s"]
    
    if item_type and item_type in ['job', 'internship']:
        where_clauses.append("a.item_type = %s")
        params.append(item_type)
    
    if status and status in ['applied', 'reviewing', 'shortlisted', 'interview', 'offer', 'hired', 'rejected', 'accepted']:
        where_clauses.append("a.status = %s")
        params.append(status)
    
    query = f"""
        SELECT 
            a.application_id, a.item_type, a.item_id, a.resume_path,
            a.cover_letter, a.status, a.applied_at, a.updated_at,
            CASE 
                WHEN a.item_type = 'job' THEN j.title
                WHEN a.item_type = 'internship' THEN i.title
            END as title,
            CASE 
                WHEN a.item_type = 'job' THEN j.location
                WHEN a.item_type = 'internship' THEN i.location
            END as location,
            CASE 
                WHEN a.item_type = 'job' THEN r1.company_name
                WHEN a.item_type = 'internship' THEN r2.company_name
            END as company_name
        FROM applications a
        LEFT JOIN jobs j ON a.item_type = 'job' AND a.item_id = j.job_id
        LEFT JOIN internships i ON a.item_type = 'internship' AND a.item_id = i.internship_id
        LEFT JOIN recruiters r1 ON j.recruiter_id = r1.recruiter_id
        LEFT JOIN recruiters r2 ON i.recruiter_id = r2.recruiter_id
        WHERE {' AND '.join(where_clauses)}
        ORDER BY a.applied_at DESC
        LIMIT %s OFFSET %s
    """
    params.extend([per_page, offset])
    
    return execute_query(query, tuple(params), fetch_all=True) or []


def get_application_by_id(application_id, user_id=None):
    """Get application details by ID."""
    params = [application_id]
    where_clause = "a.application_id = %s"
    
    if user_id:
        where_clause += " AND a.user_id = %s"
        params.append(user_id)
    
    query = f"""
        SELECT 
            a.*,
            CASE 
                WHEN a.item_type = 'job' THEN j.title
                WHEN a.item_type = 'internship' THEN i.title
            END as title,
            CASE 
                WHEN a.item_type = 'job' THEN j.location
                WHEN a.item_type = 'internship' THEN i.location
            END as location,
            CASE 
                WHEN a.item_type = 'job' THEN j.description
                WHEN a.item_type = 'internship' THEN i.description
            END as description,
            CASE 
                WHEN a.item_type = 'job' THEN r1.company_name
                WHEN a.item_type = 'internship' THEN r2.company_name
            END as company_name
        FROM applications a
        LEFT JOIN jobs j ON a.item_type = 'job' AND a.item_id = j.job_id
        LEFT JOIN internships i ON a.item_type = 'internship' AND a.item_id = i.internship_id
        LEFT JOIN recruiters r1 ON j.recruiter_id = r1.recruiter_id
        LEFT JOIN recruiters r2 ON i.recruiter_id = r2.recruiter_id
        WHERE {where_clause}
    """
    
    return execute_query(query, tuple(params), fetch_one=True)


def get_application_counts(user_id):
    """Get application counts by status for a user."""
    query = """
        SELECT status, COUNT(*) as count
        FROM applications
        WHERE user_id = %s
        GROUP BY status
    """
    results = execute_query(query, (user_id,), fetch_all=True) or []
    counts = {r['status']: r['count'] for r in results}
    return {
        'total': sum(counts.values()),
        'applied': counts.get('applied', 0),
        'reviewing': counts.get('reviewing', 0),
        'shortlisted': counts.get('shortlisted', 0),
        'rejected': counts.get('rejected', 0),
        'accepted': counts.get('accepted', 0)
    }
    
    
def auto_delete_other_applications(user_id, accepted_application_id, accepted_item_type):
    """
    Automatically delete other pending applications when one is accepted.
    Only applies to Jobs and Internships.
    """
    if accepted_item_type not in ['job', 'internship']:
        print(f"DEBUG: Auto-delete skipped for type {accepted_item_type}")
        return 0
        
    # Delete other pending applications for jobs/internships
    query = """
        DELETE FROM applications 
        WHERE user_id = %s 
        AND application_id != %s
        AND item_type IN ('job', 'internship')
        AND status IN ('applied', 'reviewing', 'shortlisted')
    """
    return execute_update(query, (user_id, accepted_application_id))


def withdraw_application(user_id, application_id):
    """
    Withdraw/Cancel an application.
    Allowed only if status is 'applied', 'reviewing', or 'shortlisted'.
    """
    # Get application to verify ownership and status
    app = get_application_by_id(application_id, user_id)
    if not app:
        return False, "Application not found"
        
    if app['status'] in ['accepted', 'rejected']:
        return False, "Cannot withdraw application that has already been processed"
        
    # Delete application (this removes it from recruiter view too)
    query = "DELETE FROM applications WHERE application_id = %s"
    rows = execute_update(query, (application_id,))
    
    if rows > 0:
        return True, "Application withdrawn successfully"
    return False, "Failed to withdraw application"
