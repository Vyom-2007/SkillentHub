"""
Recruiter service.
Handles dashboard statistics and recruiter-related operations using raw SQL.
"""
from app.database.connection import execute_query
from datetime import datetime, timedelta
from flask import current_app
import logging

def get_dashboard_stats(recruiter_id):
    """
    Get dashboard statistics for a recruiter.
    Returns counts, time-based metrics, and recent applications.
    """
    stats = {}
    try:
        # Total Jobs
        query = "SELECT COUNT(*) as count FROM jobs WHERE recruiter_id = %s"
        result = execute_query(query, (recruiter_id,), fetch_one=True)
        stats['total_jobs'] = result['count'] if result else 0
        
        # Total Internships
        query = "SELECT COUNT(*) as count FROM internships WHERE recruiter_id = %s"
        result = execute_query(query, (recruiter_id,), fetch_one=True)
        stats['total_internships'] = result['count'] if result else 0
        
        # Total Competitions
        query = "SELECT COUNT(*) as count FROM competitions WHERE recruiter_id = %s"
        result = execute_query(query, (recruiter_id,), fetch_one=True)
        stats['total_competitions'] = result['count'] if result else 0
        
        # Total Hackathons
        query = "SELECT COUNT(*) as count FROM hackathons WHERE recruiter_id = %s"
        result = execute_query(query, (recruiter_id,), fetch_one=True)
        stats['total_hackathons'] = result['count'] if result else 0
        
        # Total Applications (across all items belonging to this recruiter)
        query = """
            SELECT COUNT(*) as count FROM applications a
            WHERE (
                (a.item_type = 'job' AND a.item_id IN (SELECT job_id FROM jobs WHERE recruiter_id = %s))
                OR (a.item_type = 'internship' AND a.item_id IN (SELECT internship_id FROM internships WHERE recruiter_id = %s))
                OR (a.item_type = 'competition' AND a.item_id IN (SELECT competition_id FROM competitions WHERE recruiter_id = %s))
                OR (a.item_type = 'hackathon' AND a.item_id IN (SELECT hackathon_id FROM hackathons WHERE recruiter_id = %s))
            )
        """
        result = execute_query(query, (recruiter_id, recruiter_id, recruiter_id, recruiter_id), fetch_one=True)
        stats['total_applications'] = result['count'] if result else 0
        
        # Applications this week
        query = """
            SELECT COUNT(*) as count FROM applications a
            WHERE a.applied_at >= DATE_SUB(NOW(), INTERVAL 1 WEEK)
            AND (
                (a.item_type = 'job' AND a.item_id IN (SELECT job_id FROM jobs WHERE recruiter_id = %s))
                OR (a.item_type = 'internship' AND a.item_id IN (SELECT internship_id FROM internships WHERE recruiter_id = %s))
                OR (a.item_type = 'competition' AND a.item_id IN (SELECT competition_id FROM competitions WHERE recruiter_id = %s))
                OR (a.item_type = 'hackathon' AND a.item_id IN (SELECT hackathon_id FROM hackathons WHERE recruiter_id = %s))
            )
        """
        result = execute_query(query, (recruiter_id, recruiter_id, recruiter_id, recruiter_id), fetch_one=True)
        stats['applications_this_week'] = result['count'] if result else 0
        
        # New applications in last 24 hours
        query = """
            SELECT COUNT(*) as count FROM applications a
            WHERE a.applied_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            AND (
                (a.item_type = 'job' AND a.item_id IN (SELECT job_id FROM jobs WHERE recruiter_id = %s))
                OR (a.item_type = 'internship' AND a.item_id IN (SELECT internship_id FROM internships WHERE recruiter_id = %s))
                OR (a.item_type = 'competition' AND a.item_id IN (SELECT competition_id FROM competitions WHERE recruiter_id = %s))
                OR (a.item_type = 'hackathon' AND a.item_id IN (SELECT hackathon_id FROM hackathons WHERE recruiter_id = %s))
            )
        """
        result = execute_query(query, (recruiter_id, recruiter_id, recruiter_id, recruiter_id), fetch_one=True)
        stats['new_applications_24h'] = result['count'] if result else 0
        
        # Recent applications (last 5)
        stats['recent_applications'] = get_recent_applications(recruiter_id, limit=5)
        
        return stats
    
    except Exception as e:
        logging.error(f"Error fetching dashboard stats for recruiter {recruiter_id}: {e}")
        # Return safe defaults to prevent page crash
        return {
            'total_jobs': 0,
            'total_internships': 0,
            'total_competitions': 0,
            'total_hackathons': 0,
            'total_applications': 0,
            'applications_this_week': 0,
            'new_applications_24h': 0,
            'recent_applications': []
        }

def get_recent_applications(recruiter_id, limit=5):
    """
    Get recent applications for recruiter's postings.
    Retrieves candidate info and item details.
    """
    query = """
        SELECT 
            a.application_id,
            a.item_type,
            a.item_id,
            a.status,
            a.applied_at,
            u.user_id,
            p.full_name as candidate_name,
            p.profile_picture as profile_photo
        FROM applications a
        JOIN users u ON a.user_id = u.user_id
        LEFT JOIN profiles p ON u.user_id = p.user_id
        WHERE (
            (a.item_type = 'job' AND a.item_id IN (SELECT job_id FROM jobs WHERE recruiter_id = %s))
            OR (a.item_type = 'internship' AND a.item_id IN (SELECT internship_id FROM internships WHERE recruiter_id = %s))
            OR (a.item_type = 'competition' AND a.item_id IN (SELECT competition_id FROM competitions WHERE recruiter_id = %s))
            OR (a.item_type = 'hackathon' AND a.item_id IN (SELECT hackathon_id FROM hackathons WHERE recruiter_id = %s))
        )
        ORDER BY a.applied_at DESC
        LIMIT %s
    """
    applications = execute_query(query, (recruiter_id, recruiter_id, recruiter_id, recruiter_id, limit), fetch_all=True)
    
    # Enrich with item titles
    if applications:
        for app in applications:
            app['item_title'] = get_item_title(app['item_type'], app['item_id'])
            app['time_ago'] = get_time_ago(app['applied_at'])
    else:
        applications = []
    
    return applications


def get_item_title(item_type, item_id):
    """Get the title of an item based on its type and ID."""
    table_map = {
        'job': ('jobs', 'job_id', 'title'),
        'internship': ('internships', 'internship_id', 'title'),
        'competition': ('competitions', 'competition_id', 'title'),
        'hackathon': ('hackathons', 'hackathon_id', 'title')
    }
    
    if item_type not in table_map:
        return 'Unknown Item'
    
    table, id_col, title_col = table_map[item_type]
    query = f"SELECT {title_col} FROM {table} WHERE {id_col} = %s"
    result = execute_query(query, (item_id,), fetch_one=True)
    
    return result[title_col] if result else 'Unknown Item'


def get_time_ago(dt):
    """Convert datetime to human-readable time ago string."""
    if not dt:
        return 'Unknown'
    
    now = datetime.now()
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    
    diff = now - dt
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return 'Just now'
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f'{minutes} min{"s" if minutes > 1 else ""} ago'
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f'{hours} hour{"s" if hours > 1 else ""} ago'
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f'{days} day{"s" if days > 1 else ""} ago'
    else:
        weeks = int(seconds / 604800)
        return f'{weeks} week{"s" if weeks > 1 else ""} ago'


def get_all_applications(recruiter_id, status=None, item_type=None, page=1, per_page=20):
    """
    Get all applications for recruiter's postings with pagination.
    """
    base_query = """
        SELECT 
            a.application_id,
            a.item_type,
            a.item_id,
            a.status,
            a.applied_at,
            a.cover_letter,
            u.user_id,
            p.full_name as candidate_name,
            u.email as candidate_email,
            p.profile_picture as profile_photo,
            p.headline
        FROM applications a
        JOIN users u ON a.user_id = u.user_id
        LEFT JOIN profiles p ON u.user_id = p.user_id
        WHERE (
            (a.item_type = 'job' AND a.item_id IN (SELECT job_id FROM jobs WHERE recruiter_id = %s))
            OR (a.item_type = 'internship' AND a.item_id IN (SELECT internship_id FROM internships WHERE recruiter_id = %s))
            OR (a.item_type = 'competition' AND a.item_id IN (SELECT competition_id FROM competitions WHERE recruiter_id = %s))
            OR (a.item_type = 'hackathon' AND a.item_id IN (SELECT hackathon_id FROM hackathons WHERE recruiter_id = %s))
        )
    """
    params = [recruiter_id, recruiter_id, recruiter_id, recruiter_id]
    
    if status:
        base_query += " AND a.status = %s"
        params.append(status)
    
    if item_type:
        base_query += " AND a.item_type = %s"
        params.append(item_type)
    
    base_query += " ORDER BY a.applied_at DESC LIMIT %s OFFSET %s"
    params.extend([per_page, (page - 1) * per_page])
    
    applications = execute_query(base_query, tuple(params))
    
    for app in applications:
        app['item_title'] = get_item_title(app['item_type'], app['item_id'])
        app['time_ago'] = get_time_ago(app['applied_at'])
    
    return applications


def update_application_status(application_id, new_status, recruiter_id):
    """
    Update application status.
    Verifies the application belongs to recruiter's posting.
    """
    from app.database.connection import execute_update
    
    # Verify ownership
    query = """
        SELECT a.application_id FROM applications a
        WHERE a.application_id = %s AND (
            (a.item_type = 'job' AND a.item_id IN (SELECT job_id FROM jobs WHERE recruiter_id = %s))
            OR (a.item_type = 'internship' AND a.item_id IN (SELECT internship_id FROM internships WHERE recruiter_id = %s))
            OR (a.item_type = 'competition' AND a.item_id IN (SELECT competition_id FROM competitions WHERE recruiter_id = %s))
            OR (a.item_type = 'hackathon' AND a.item_id IN (SELECT hackathon_id FROM hackathons WHERE recruiter_id = %s))
        )
    """
    result = execute_query(query, (application_id, recruiter_id, recruiter_id, recruiter_id, recruiter_id), fetch_one=True)
    
    if not result:
        return False, "Application not found or access denied"
    
    # Update status
    update_query = "UPDATE applications SET status = %s WHERE application_id = %s"
    rows = execute_update(update_query, (new_status, application_id))
    
    if rows:
        return True, "Status updated successfully"
    return False, "Failed to update status"
