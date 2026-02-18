"""
Recruiter service.
Handles dashboard statistics and recruiter-related operations using raw SQL.
"""
from app.database.connection import execute_query, execute_update
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
        # We need to count from applications AND registrations tables
        query = """
            SELECT (
                (SELECT COUNT(*) FROM applications a
                 WHERE (
                    (a.item_type = 'job' AND a.item_id IN (SELECT job_id FROM jobs WHERE recruiter_id = %s))
                    OR (a.item_type = 'internship' AND a.item_id IN (SELECT internship_id FROM internships WHERE recruiter_id = %s))
                    OR (a.item_type = 'competition' AND a.item_id IN (SELECT competition_id FROM competitions WHERE recruiter_id = %s))
                    OR (a.item_type = 'hackathon' AND a.item_id IN (SELECT hackathon_id FROM hackathons WHERE recruiter_id = %s))
                 ))
                +
                (SELECT COUNT(*) FROM hackathon_registrations hr
                 JOIN hackathons h ON hr.hackathon_id = h.hackathon_id
                 WHERE h.recruiter_id = %s)
                +
                (SELECT COUNT(*) FROM competition_registrations cr
                 JOIN competitions c ON cr.competition_id = c.competition_id
                 WHERE c.recruiter_id = %s)
            ) as count
        """
        # Params: 4 for app, 1 for hack, 1 for comp
        params = (recruiter_id, recruiter_id, recruiter_id, recruiter_id, recruiter_id, recruiter_id)
        result = execute_query(query, params, fetch_one=True)
        stats['total_applications'] = result['count'] if result else 0
        
        # Applications this week
        query = """
            SELECT (
                (SELECT COUNT(*) FROM applications a
                 WHERE a.applied_at >= DATE_SUB(NOW(), INTERVAL 1 WEEK)
                 AND (
                    (a.item_type = 'job' AND a.item_id IN (SELECT job_id FROM jobs WHERE recruiter_id = %s))
                    OR (a.item_type = 'internship' AND a.item_id IN (SELECT internship_id FROM internships WHERE recruiter_id = %s))
                    OR (a.item_type = 'competition' AND a.item_id IN (SELECT competition_id FROM competitions WHERE recruiter_id = %s))
                    OR (a.item_type = 'hackathon' AND a.item_id IN (SELECT hackathon_id FROM hackathons WHERE recruiter_id = %s))
                 ))
                +
                (SELECT COUNT(*) FROM hackathon_registrations hr
                 JOIN hackathons h ON hr.hackathon_id = h.hackathon_id
                 WHERE hr.registered_at >= DATE_SUB(NOW(), INTERVAL 1 WEEK) AND h.recruiter_id = %s)
                +
                (SELECT COUNT(*) FROM competition_registrations cr
                 JOIN competitions c ON cr.competition_id = c.competition_id
                 WHERE cr.registered_at >= DATE_SUB(NOW(), INTERVAL 1 WEEK) AND c.recruiter_id = %s)
            ) as count
        """
        result = execute_query(query, params, fetch_one=True)
        stats['applications_this_week'] = result['count'] if result else 0
        
        # New applications in last 24 hours
        query = """
            SELECT (
                (SELECT COUNT(*) FROM applications a
                 WHERE a.applied_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                 AND (
                    (a.item_type = 'job' AND a.item_id IN (SELECT job_id FROM jobs WHERE recruiter_id = %s))
                    OR (a.item_type = 'internship' AND a.item_id IN (SELECT internship_id FROM internships WHERE recruiter_id = %s))
                    OR (a.item_type = 'competition' AND a.item_id IN (SELECT competition_id FROM competitions WHERE recruiter_id = %s))
                    OR (a.item_type = 'hackathon' AND a.item_id IN (SELECT hackathon_id FROM hackathons WHERE recruiter_id = %s))
                 ))
                +
                (SELECT COUNT(*) FROM hackathon_registrations hr
                 JOIN hackathons h ON hr.hackathon_id = h.hackathon_id
                 WHERE hr.registered_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR) AND h.recruiter_id = %s)
                +
                (SELECT COUNT(*) FROM competition_registrations cr
                 JOIN competitions c ON cr.competition_id = c.competition_id
                 WHERE cr.registered_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR) AND c.recruiter_id = %s)
            ) as count
        """
        result = execute_query(query, params, fetch_one=True)
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
    Get recent applications AND registrations for recruiter's postings.
    Unions data from:
    1. applications table
    2. hackathon_registrations table
    3. competition_registrations table
    """
    query = """
        SELECT * FROM (
            -- 1. Applications
            SELECT 
                a.application_id as id,
                a.item_type,
                a.item_id,
                a.status,
                a.applied_at as date,
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

            UNION ALL

            -- 2. Hackathon Registrations
            SELECT 
                hr.registration_id as id,
                'hackathon' as item_type,
                hr.hackathon_id as item_id,
                'registered' as status,
                hr.registered_at as date,
                u.user_id,
                COALESCE(hr.name, p.full_name, 'Unknown') as candidate_name,
                p.profile_picture as profile_photo
            FROM hackathon_registrations hr
            JOIN hackathons h ON hr.hackathon_id = h.hackathon_id
            LEFT JOIN users u ON hr.user_id = u.user_id
            LEFT JOIN profiles p ON u.user_id = p.user_id
            WHERE h.recruiter_id = %s

            UNION ALL

            -- 3. Competition Registrations
            SELECT 
                cr.registration_id as id,
                'competition' as item_type,
                cr.competition_id as item_id,
                'registered' as status,
                cr.registered_at as date,
                u.user_id,
                p.full_name as candidate_name,
                p.profile_picture as profile_photo
            FROM competition_registrations cr
            JOIN competitions c ON cr.competition_id = c.competition_id
            LEFT JOIN users u ON cr.user_id = u.user_id
            LEFT JOIN profiles p ON u.user_id = p.user_id
            WHERE c.recruiter_id = %s

        ) AS combined_activity
        ORDER BY date DESC
        LIMIT %s
    """
    
    # Params: 4 for applications, 1 for hackathons, 1 for competitions, 1 for limit
    params = (recruiter_id, recruiter_id, recruiter_id, recruiter_id, recruiter_id, recruiter_id, limit)
    
    applications = execute_query(query, params, fetch_all=True)
    
    # Enrich with item titles
    if applications:
        for app in applications:
            app['item_title'] = get_item_title(app['item_type'], app['item_id'])
            app['time_ago'] = get_time_ago(app['date'])
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
    if rows:
        # Log Activity if hired/accepted
        if new_status in ['hired', 'accepted']:
            try:
                from app.services import activity_service
                # Need to find which user was hired.
                # Query above didn't return user_id, let's fetch it.
                user_check = execute_query("SELECT user_id, item_type, item_id FROM applications WHERE application_id = %s", (application_id,), fetch_one=True)
                if user_check:
                    activity_service.log_activity(
                        action_type='user_hired',
                        recruiter_id=recruiter_id,
                        user_id=user_check['user_id'],
                        item_type='application',
                        item_id=application_id,
                        details={'status': new_status, 'item_type': user_check['item_type'], 'item_id': user_check['item_id']}
                    )
            except Exception as e:
                logging.error(f"Error logging hire activity: {e}")
                
        return True, "Status updated successfully"
    return False, "Failed to update status"


def save_candidate(recruiter_id, user_id, note=None):
    """Save a candidate profile."""
    # Ensure user exists
    check_user = execute_query("SELECT 1 FROM users WHERE user_id = %s", (user_id,), fetch_one=True)
    if not check_user:
        return False, "User not found"
        
    query = """
        INSERT IGNORE INTO saved_candidates (recruiter_id, user_id, note)
        VALUES (%s, %s, %s)
    """
    execute_update(query, (recruiter_id, user_id, note))
    return True, "Candidate saved successfully"


def unsave_candidate(recruiter_id, user_id):
    """Unsave a candidate."""
    query = "DELETE FROM saved_candidates WHERE recruiter_id = %s AND user_id = %s"
    execute_update(query, (recruiter_id, user_id))
    return True, "Candidate removed from saved list"


def get_saved_candidates(recruiter_id):
    """Get all saved candidates for a recruiter."""
    query = """
        SELECT s.save_id, s.user_id, s.note, s.saved_at,
               p.full_name, p.headline, p.profile_picture, p.location,
               u.email
        FROM saved_candidates s
        JOIN users u ON s.user_id = u.user_id
        LEFT JOIN profiles p ON u.user_id = p.user_id
        WHERE s.recruiter_id = %s
        ORDER BY s.saved_at DESC
    """
    return execute_query(query, (recruiter_id,), fetch_all=True) or []


def is_candidate_saved(recruiter_id, user_id):
    """Check if candidate is saved."""
    query = "SELECT 1 FROM saved_candidates WHERE recruiter_id = %s AND user_id = %s"
    result = execute_query(query, (recruiter_id, user_id), fetch_one=True)
    return bool(result)


def get_analytics_stats(recruiter_id):
    """
    Get analytics for recruiter dashboard.
    Returns:
        dict: {
            'top_jobs': [{'title': str, 'count': int}, ...],
            'funnel': {'total': int, 'reviewing': int, 'shortlisted': int, 'hired': int},
            'time_to_hire': float (days)
        }
    """
    stats = {
        'top_jobs': [],
        'funnel': {'total': 0, 'reviewing': 0, 'shortlisted': 0, 'hired': 0},
        'time_to_hire': 0
    }
    
    try:
        # 1. Top 5 Jobs by Applications
        # Just jobs for now as per plan
        job_query = """
            SELECT j.title, COUNT(a.application_id) as count
            FROM jobs j
            LEFT JOIN applications a ON j.job_id = a.item_id AND a.item_type = 'job'
            WHERE j.recruiter_id = %s
            GROUP BY j.job_id
            ORDER BY count DESC
            LIMIT 5
        """
        top_jobs = execute_query(job_query, (recruiter_id,), fetch_all=True)
        stats['top_jobs'] = top_jobs if top_jobs else []
        
        # 2. Funnel Stats (Global for all items)
        funnel_query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status IN ('reviewing', 'shortlisted', 'accepted') THEN 1 ELSE 0 END) as reviewing,
                SUM(CASE WHEN status IN ('shortlisted', 'accepted') THEN 1 ELSE 0 END) as shortlisted,
                SUM(CASE WHEN status = 'accepted' THEN 1 ELSE 0 END) as hired
            FROM applications a
            WHERE (
                (a.item_type = 'job' AND a.item_id IN (SELECT job_id FROM jobs WHERE recruiter_id = %s))
                OR (a.item_type = 'internship' AND a.item_id IN (SELECT internship_id FROM internships WHERE recruiter_id = %s))
                OR (a.item_type = 'competition' AND a.item_id IN (SELECT competition_id FROM competitions WHERE recruiter_id = %s))
                OR (a.item_type = 'hackathon' AND a.item_id IN (SELECT hackathon_id FROM hackathons WHERE recruiter_id = %s))
            )
        """
        funnel = execute_query(funnel_query, (recruiter_id, recruiter_id, recruiter_id, recruiter_id), fetch_one=True)
        if funnel:
            # Decimal to int conversion if needed, though pymysql usually handles returns well
            stats['funnel'] = {
                'total': int(funnel['total'] or 0),
                'reviewing': int(funnel['reviewing'] or 0),
                'shortlisted': int(funnel['shortlisted'] or 0),
                'hired': int(funnel['hired'] or 0)
            }
            
        # 3. Time to Hire
        # Average time from applied_at to updated_at for 'accepted' status
        tth_query = """
            SELECT AVG(DATEDIFF(updated_at, applied_at)) as avg_days
            FROM applications a
            WHERE status = 'accepted'
            AND (
                (a.item_type = 'job' AND a.item_id IN (SELECT job_id FROM jobs WHERE recruiter_id = %s))
                OR (a.item_type = 'internship' AND a.item_id IN (SELECT internship_id FROM internships WHERE recruiter_id = %s))
            )
        """
        tth = execute_query(tth_query, (recruiter_id, recruiter_id), fetch_one=True)
        if tth and tth['avg_days'] is not None:
             stats['time_to_hire'] = round(float(tth['avg_days']), 1)
             
    except Exception as e:
        logging.error(f"Error fetching analytics for recruiter {recruiter_id}: {e}")
        
    return stats
