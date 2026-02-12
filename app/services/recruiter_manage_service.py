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
    Fetch applications AND registrations (Unified ATS).
    """
    # 1. Applications Query
    # Note: We use p.full_name for candidates.
    app_query = """
        SELECT 
            a.application_id, 
            a.item_type, 
            a.item_id, 
            a.status, 
            a.applied_at as date,
            p.full_name, 
            u.email,
            p.profile_picture,
            COALESCE(j.title, i.title, c.title, h.title) as item_title,
            NULL as team_name
        FROM applications a
        JOIN users u ON a.user_id = u.user_id
        LEFT JOIN profiles p ON u.user_id = p.user_id
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
    app_params = [recruiter_id, recruiter_id, recruiter_id, recruiter_id]
    
    # 2. Hackathon Registrations Query
    # registration_id -> application_id
    # 'registered' -> status (dummy)
    # registered_at -> date
    # COALESCE(hr.name, p.full_name) -> full_name (handles guests)
    # COALESCE(hr.email, u.email) -> email (handles guests)
    hack_query = """
        SELECT 
            hr.registration_id as application_id, 
            'hackathon' as item_type, 
            hr.hackathon_id as item_id, 
            'registered' as status, 
            hr.registered_at as date,
            COALESCE(p.full_name, hr.name, 'Guest') as full_name, 
            COALESCE(u.email, hr.email, 'No Email') as email,
            p.profile_picture,
            h.title as item_title,
            hr.team_name
        FROM hackathon_registrations hr
        JOIN hackathons h ON hr.hackathon_id = h.hackathon_id
        LEFT JOIN users u ON hr.user_id = u.user_id
        LEFT JOIN profiles p ON u.user_id = p.user_id
        WHERE h.recruiter_id = %s
    """
    hack_params = [recruiter_id]

    # 3. Competition Registrations Query
    comp_query = """
        SELECT 
            cr.registration_id as application_id, 
            'competition' as item_type, 
            cr.competition_id as item_id, 
            'registered' as status, 
            cr.registered_at as date,
            p.full_name, 
            u.email,
            p.profile_picture,
            c.title as item_title,
            NULL as team_name
        FROM competition_registrations cr
        JOIN competitions c ON cr.competition_id = c.competition_id
        JOIN users u ON cr.user_id = u.user_id
        LEFT JOIN profiles p ON u.user_id = p.user_id
        WHERE c.recruiter_id = %s
    """
    comp_params = [recruiter_id]

    # Apply Filters (Harder with UNION, but possible by wrapping)
    # For simplicity, we filter AFTER union in SQL or construct WHERE clauses.
    # Given the complexity, wrapping is cleaner.
    
    full_query = f"""
        SELECT * FROM (
            {app_query}
            UNION ALL
            {hack_query}
            UNION ALL
            {comp_query}
        ) as unified
        WHERE 1=1
    """
    
    all_params = app_params + hack_params + comp_params
    
    if filters:
        if filters.get('status'):
            # Note: Event registrations will only show up if status='registered' (or whatever we set)
            full_query += " AND status = %s"
            all_params.append(filters['status'])
            
        if filters.get('item_type'):
            full_query += " AND item_type = %s"
            all_params.append(filters['item_type'])
            
    full_query += " ORDER BY applied_at DESC"
    
    # Execute with fetch_all names mapped correctly
    # Note: execute_query returns dicts, keys are based on alias.
    # We aliased 'applied_at' as 'date' in union. 
    # But template might expect 'applied_at'. Let's alias it as 'applied_at' in outer query or inner.
    # Let's fix aliases to match original ATS expectation: applied_at
    
    # RE-DO aliases in queries above for consistency
    # We replaced " as date" with " as applied_at" in the return call, but that only affects the string passed to execute_query if done there.
    # But the ORDER BY clause was appended to `full_query` before the replacement.
    # And `full_query` uses `ORDER BY date DESC`. 
    # The replacement `full_query.replace(" as date", " as applied_at")` would change inner aliases to `applied_at`.
    # But filters might use `date`? No, filters use `status` and `item_type`.
    # The ORDER BY clause `ORDER BY date DESC` would fail if `date` is replaced by `applied_at`.
    # Let's simple use "applied_at" everywhere in the string construction or just do the replacement safely.
    
    final_sql = full_query.replace(" as date", " as applied_at").replace("ORDER BY date", "ORDER BY applied_at")
    
    return execute_query(final_sql, tuple(all_params), fetch_all=True)

def get_application_detail(application_id, recruiter_id):
    """
    Fetch full application details, ensuring recruiter ownership.
    """
    # Reuse list query structure but filter by app ID
    query = """
    SELECT 
        a.*,
        p.full_name, u.email, u.user_id as applicant_id,
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
                    a.user_id,
                    a.item_type,
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
                # Send email
                from app.services.email_service import send_status_update_email
                send_status_update_email(
                    to_email=details['email'],
                    candidate_name=details['candidate_name'] or "Candidate",
                    item_title=details['item_title'] or "Position",
                    company_name=details['company_name'] or "SkillentHub Recruiter",
                    status=new_status,
                    application_id=application_id
                )
                
                # Auto-reject other applications if accepted
                if new_status == 'accepted':
                    from app.services import application_service
                    application_service.auto_reject_other_applications(
                        user_id=details['user_id'],
                        accepted_application_id=application_id,
                        accepted_item_type=details['item_type']
                    )
                    
        except Exception as e:
            # Log error but don't fail the status update
            print(f"Error handling status update side effects: {e}")
            from flask import current_app
            current_app.logger.error(f"Error handling status update for app {application_id}: {e}")
        
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
