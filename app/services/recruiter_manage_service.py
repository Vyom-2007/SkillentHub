"""
Recruiter Management Service.
Handles managing opportunities (View/Edit/Delete) and ATS (Applications).
"""
from app.database.connection import execute_query, execute_insert, execute_update
from datetime import datetime

# --- OPPORTUNITY MANAGEMENT ---

def get_posted_opportunities(recruiter_id, status_filter=None, search_query=None):
    """
    Fetch all jobs, internships, competitions, and hackathons posted by the recruiter.
    Returns a unified list sorted by date descending.
    """
    # Helper to build subquery for each type
    def build_select(table, type_name, id_col, date_col):
        # Handle difference in status column availability
        status_col = "status" if table in ['jobs', 'internships'] else "'active'"
        
        sql = f"""
            SELECT 
                {id_col} as id,
                '{type_name}' as type,
                title,
                {date_col} as created_at,
                is_active,
                {status_col} as status,
                (SELECT COUNT(*) FROM applications WHERE item_type = '{type_name}' AND item_id = {table}.{id_col}) as app_count
            FROM {table}
            WHERE recruiter_id = %s
        """
        if status_filter:
            if status_filter == 'active':
                 sql += " AND is_active = 1"
            elif status_filter == 'inactive':
                 sql += " AND is_active = 0"
        
        if search_query:
            sql += f" AND title LIKE '%%{search_query}%%'"
            
        return sql

    # Build UNION query
    queries = [
        build_select('jobs', 'job', 'job_id', 'posted_at'),
        build_select('internships', 'internship', 'internship_id', 'posted_at'),
        build_select('competitions', 'competition', 'competition_id', 'created_at'),
        build_select('hackathons', 'hackathon', 'hackathon_id', 'created_at')
    ]
    
    final_query = " UNION ALL ".join(queries) + " ORDER BY created_at DESC"
    
    # Execute (params repeated 4 times)
    params = (recruiter_id, recruiter_id, recruiter_id, recruiter_id)
    return execute_query(final_query, params)

def toggle_opportunity_status(item_type, item_id, recruiter_id):
    """
    Toggle is_active status of an item.
    """
    table_map = {
        'job': 'jobs', 'internship': 'internships', 
        'competition': 'competitions', 'hackathon': 'hackathons'
    }
    id_col_map = {
        'job': 'job_id', 'internship': 'internship_id', 
        'competition': 'competition_id', 'hackathon': 'hackathon_id'
    }
    
    if item_type not in table_map:
        return False
        
    table = table_map[item_type]
    id_col = id_col_map[item_type]
    
    # Check current status
    check_sql = f"SELECT is_active FROM {table} WHERE {id_col} = %s AND recruiter_id = %s"
    current = execute_query(check_sql, (item_id, recruiter_id), fetch_one=True)
    
    if not current:
        return False
        
    new_status = 0 if current['is_active'] else 1
    update_sql = f"UPDATE {table} SET is_active = %s WHERE {id_col} = %s AND recruiter_id = %s"
    return execute_update(update_sql, (new_status, item_id, recruiter_id)) > 0


# --- ATS (APPLICATION TRACKING) ---

def get_applications(recruiter_id, filters=None):
    """
    Fetch applications with Candidate Details and Item Titles.
    Performs JOINs to access mapped tables.
    """
    params = []
    
    # CTE or Complex Join approach?
    # Since we need to join on different tables based on item_type, 
    # and we need to filter by recruiter_id which is in those tables.
    
    query = """
    SELECT 
        a.application_id, a.item_type, a.item_id, a.status, a.applied_at,
        u.first_name, u.last_name, u.email,
        p.profile_picture,
        COALESCE(j.title, i.title, c.title, h.title) as item_title
    FROM applications a
    JOIN users u ON a.user_id = u.user_id
    LEFT JOIN profiles p ON u.user_id = p.user_id
    
    -- LEFT JOINS to get Titles and Check Recruiter ID
    LEFT JOIN jobs j ON a.item_type = 'job' AND a.item_id = j.job_id
    LEFT JOIN internships i ON a.item_type = 'internship' AND a.item_id = i.internship_id
    LEFT JOIN competitions c ON a.item_type = 'competition' AND a.item_id = c.competition_id
    LEFT JOIN hackathons h ON a.item_type = 'hackathon' AND a.item_id = h.hackathon_id
    
    WHERE (
        (j.recruiter_id = %s) OR 
        (i.recruiter_id = %s) OR 
        (c.recruiter_id = %s) OR 
        (h.recruiter_id = %s)
    )
    """
    params.extend([recruiter_id, recruiter_id, recruiter_id, recruiter_id])
    
    if filters:
        if filters.get('status'):
            query += " AND a.status = %s"
            params.append(filters['status'])
            
        if filters.get('item_type'):
            query += " AND a.item_type = %s"
            params.append(filters['item_type'])
            
    query += " ORDER BY a.applied_at DESC"
    
    return execute_query(query, tuple(params))

def get_application_detail(application_id, recruiter_id):
    """
    Fetch full application details, ensuring recruiter ownership.
    """
    # Reuse list query structure but filter by app ID
    query = """
    SELECT 
        a.*,
        u.first_name, u.last_name, u.email, u.user_id as applicant_id,
        p.profile_picture, p.headline, p.skills, p.city, p.state,
        COALESCE(j.title, i.title, c.title, h.title) as item_title
    FROM applications a
    JOIN users u ON a.user_id = u.user_id
    LEFT JOIN profiles p ON u.user_id = p.user_id
    
    LEFT JOIN jobs j ON a.item_type = 'job' AND a.item_id = j.job_id
    LEFT JOIN internships i ON a.item_type = 'internship' AND a.item_id = i.internship_id
    LEFT JOIN competitions c ON a.item_type = 'competition' AND a.item_id = c.competition_id
    LEFT JOIN hackathons h ON a.item_type = 'hackathon' AND a.item_id = h.hackathon_id
    
    WHERE a.application_id = %s
    AND (
        (j.recruiter_id = %s) OR 
        (i.recruiter_id = %s) OR 
        (c.recruiter_id = %s) OR 
        (h.recruiter_id = %s)
    )
    """
    return execute_query(query, (application_id, recruiter_id, recruiter_id, recruiter_id, recruiter_id), fetch_one=True)

def update_application_status(application_id, new_status, recruiter_id=None):
    """
    Update status and trigger email if Shortlisted/Accepted.
    """
    query = "UPDATE applications SET status = %s, updated_at = NOW() WHERE application_id = %s"
    result = execute_update(query, (new_status, application_id))
    
    if result and new_status in ['shortlisted', 'accepted']:
        try:
            # Fetch details for email
            fetch_sql = """
                SELECT 
                    u.email, 
                    p.full_name as candidate_name,
                    COALESCE(j.title, i.title, c.title, h.title) as item_title,
                    r.company_name
                FROM applications a
                JOIN users u ON a.user_id = u.user_id
                LEFT JOIN profiles p ON u.user_id = p.user_id
                LEFT JOIN jobs j ON a.item_type = 'job' AND a.item_id = j.job_id
                LEFT JOIN internships i ON a.item_type = 'internship' AND a.item_id = i.internship_id
                LEFT JOIN competitions c ON a.item_type = 'competition' AND a.item_id = c.competition_id
                LEFT JOIN hackathons h ON a.item_type = 'hackathon' AND a.item_id = h.hackathon_id
                LEFT JOIN recruiters r ON r.recruiter_id = COALESCE(j.recruiter_id, i.recruiter_id, c.recruiter_id, h.recruiter_id)
                WHERE a.application_id = %s
            """
            details = execute_query(fetch_sql, (application_id,), fetch_one=True)
            
            if details:
                from app.services.email_service import send_status_update_email
                send_status_update_email(
                    to_email=details['email'],
                    candidate_name=details['candidate_name'] or "Candidate",
                    item_title=details['item_title'] or "Position",
                    company_name=details['company_name'] or "SkillentHub Recruiter",
                    status=new_status,
                    application_id=application_id
                )
        except Exception as e:
            # Log error but don't fail the status update
            print(f"Error sending status email: {e}")
            from flask import current_app
            current_app.logger.error(f"Error sending status email for app {application_id}: {e}")
        
    return result

def add_note(application_id, recruiter_id, content):
    """Add an internal note."""
    query = "INSERT INTO application_notes (application_id, recruiter_id, content) VALUES (%s, %s, %s)"
    return execute_insert(query, (application_id, recruiter_id, content))

def get_notes(application_id):
    """Get internal notes for an application."""
    query = """
        SELECT n.*, r.company_name, r.first_name as recruiter_name 
        FROM application_notes n
        JOIN recruiters r ON n.recruiter_id = r.recruiter_id
        WHERE n.application_id = %s
        ORDER BY n.created_at DESC
    """
    return execute_query(query, (application_id,))
