"""
Opportunity service.
Handles jobs and internships search and filtering.
"""
from app.database.connection import execute_query
from datetime import datetime, timedelta


def _ensure_dates(item):
    """Convert date strings to datetime objects."""
    if not item:
        return item
        
    for field in ['posted_at', 'deadline', 'start_date', 'end_date']:
        if field in item and isinstance(item[field], str):
            val = item[field]
            # Try common formats
            formats = [
                '%Y-%m-%d',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%S.%f',
                '%a, %d %b %Y %H:%M:%S %Z'
            ]
            parsed = False
            for fmt in formats:
                try:
                    item[field] = datetime.strptime(val, fmt)
                    parsed = True
                    break
                except ValueError:
                    continue
            
            if not parsed:
                # If cannot parse, maybe set to None so it doesn't crash template
                # Or keep string but log warning? Safe to set None if it's junk data
                # But better to keep string for debugging? No, string crashes template.
                # Let's set to None or allow crash if it's really partial?
                # User says "Error is not solving", likely 500.
                # If we convert to None, template handles it gracefully ('Open' for deadline, etc.)
                # But for 'posted_at', sort might fail if None?
                # lambda x: x.get('posted_at') or datetime.min
                # If we set None, datetime.min is used. Safe.
                print(f"Failed to parse date: {val}")
                item[field] = None
    return item


def search_opportunities(opp_type='all', q=None, location=None, work_mode=None, 
                         job_type=None, date_posted=None, experience=None,
                         page=1, per_page=50):
    """
    Search opportunities with dynamic SQL filtering.
    
    Args:
        opp_type: 'job', 'internship', or 'all'
        q: Keyword search (title/description)
        location: Location filter
        work_mode: on-site/remote/hybrid
        job_type: full-time/part-time/contract (jobs only)
        date_posted: 7/30/90 (days)
        experience: Experience level filter (jobs only)
        page: Page number
        per_page: Results per page
    """
    offset = (page - 1) * per_page
    results = []
    
    # Fetch jobs
    if opp_type in ['job', 'all']:
        jobs = _search_jobs(q, location, work_mode, job_type, date_posted, experience, per_page, offset)
        results.extend(jobs)
    
    # Fetch internships
    if opp_type in ['internship', 'all']:
        internships = _search_internships(q, location, work_mode, date_posted, per_page, offset)
        results.extend(internships)
    
    # Sort by posted_at desc
    results.sort(key=lambda x: x.get('posted_at') or datetime.min, reverse=True)
    
    # Limit if fetching both
    if opp_type == 'all':
        results = results[:per_page]
    
    return results


def _search_jobs(q=None, location=None, work_mode=None, job_type=None, 
                 date_posted=None, experience=None, limit=50, offset=0):
    """Search jobs with dynamic filters."""
    params = []
    where_clauses = ["j.status = 'active'", "j.is_active = 1"]
    
    # Keyword search
    if q and q.strip():
        where_clauses.append("(j.title LIKE %s OR j.description LIKE %s OR j.skills_required LIKE %s)")
        search_term = f"%{q.strip()}%"
        params.extend([search_term, search_term, search_term])
    
    # Location filter
    if location and location.strip():
        where_clauses.append("j.location LIKE %s")
        params.append(f"%{location.strip()}%")
    
    # Work mode filter
    if work_mode and work_mode in ['on-site', 'remote', 'hybrid']:
        where_clauses.append("j.work_mode = %s")
        params.append(work_mode)
    
    # Job type filter
    if job_type and job_type in ['full-time', 'part-time', 'contract']:
        where_clauses.append("j.job_type = %s")
        params.append(job_type)
    
    # Date posted filter
    if date_posted:
        days = int(date_posted)
        cutoff_date = datetime.now() - timedelta(days=days)
        where_clauses.append("j.posted_at >= %s")
        params.append(cutoff_date)
    
    # Experience filter
    if experience and experience.strip():
        where_clauses.append("j.experience_required LIKE %s")
        params.append(f"%{experience.strip()}%")
    
    query = f"""
        SELECT 
            j.job_id as id, 'job' as type,
            j.title, j.location, j.job_type, j.work_mode,
            j.experience_required, j.salary_range, j.skills_required,
            j.description, j.posted_at, j.deadline, j.number_of_openings,
            r.company_name
        FROM jobs j
        LEFT JOIN recruiters r ON j.recruiter_id = r.recruiter_id
        WHERE {' AND '.join(where_clauses)}
        ORDER BY j.posted_at DESC
        LIMIT %s OFFSET %s
    """
    params.extend([limit, offset])
    
    results = execute_query(query, tuple(params), fetch_all=True) or []
    for r in results:
        _ensure_dates(r)
    return results


def _search_internships(q=None, location=None, work_mode=None, date_posted=None, 
                        limit=50, offset=0):
    """Search internships with dynamic filters."""
    params = []
    where_clauses = ["i.status = 'active'", "i.is_active = 1"]
    
    # Keyword search
    if q and q.strip():
        where_clauses.append("(i.title LIKE %s OR i.description LIKE %s OR i.skills_required LIKE %s)")
        search_term = f"%{q.strip()}%"
        params.extend([search_term, search_term, search_term])
    
    # Location filter
    if location and location.strip():
        where_clauses.append("i.location LIKE %s")
        params.append(f"%{location.strip()}%")
    
    # Work mode filter
    if work_mode and work_mode in ['on-site', 'remote', 'hybrid']:
        where_clauses.append("i.work_mode = %s")
        params.append(work_mode)
    
    # Date posted filter
    if date_posted:
        days = int(date_posted)
        cutoff_date = datetime.now() - timedelta(days=days)
        where_clauses.append("i.posted_at >= %s")
        params.append(cutoff_date)
    
    query = f"""
        SELECT 
            i.internship_id as id, 'internship' as type,
            i.title, i.location, i.duration, i.stipend, i.work_mode,
            i.certificate_provided, i.skills_required,
            i.description, i.posted_at, i.deadline,
            r.company_name
        FROM internships i
        LEFT JOIN recruiters r ON i.recruiter_id = r.recruiter_id
        WHERE {' AND '.join(where_clauses)}
        ORDER BY i.posted_at DESC
        LIMIT %s OFFSET %s
    """
    params.extend([limit, offset])
    
    results = execute_query(query, tuple(params), fetch_all=True) or []
    for r in results:
        _ensure_dates(r)
    return results


def get_job_by_id(job_id):
    """Get job details by ID."""
    query = """
        SELECT 
            j.*, r.company_name, r.company_email
        FROM jobs j
        LEFT JOIN recruiters r ON j.recruiter_id = r.recruiter_id
        WHERE j.job_id = %s
    """
    job = execute_query(query, (job_id,), fetch_one=True)
    return _ensure_dates(job)


def get_internship_by_id(internship_id):
    """Get internship details by ID."""
    query = """
        SELECT 
            i.*, r.company_name, r.company_email
        FROM internships i
        LEFT JOIN recruiters r ON i.recruiter_id = r.recruiter_id
        WHERE i.internship_id = %s
    """
    internship = execute_query(query, (internship_id,), fetch_one=True)
    return _ensure_dates(internship)


def get_all_locations():
    """Get all unique locations from jobs and internships."""
    query = """
        SELECT DISTINCT location FROM (
            SELECT location FROM jobs WHERE status = 'active' AND is_active = 1
            UNION
            SELECT location FROM internships WHERE status = 'active' AND is_active = 1
        ) as locations
        WHERE location IS NOT NULL AND location != ''
        ORDER BY location
    """
    results = execute_query(query, fetch_all=True) or []
    return [r['location'] for r in results]


def get_opportunity_counts():
    """Get counts of active opportunities."""
    jobs_count = execute_query(
        "SELECT COUNT(*) as count FROM jobs WHERE status = 'active' AND is_active = 1",
        fetch_one=True
    )
    internships_count = execute_query(
        "SELECT COUNT(*) as count FROM internships WHERE status = 'active' AND is_active = 1",
        fetch_one=True
    )
    return {
        'jobs': jobs_count['count'] if jobs_count else 0,
        'internships': internships_count['count'] if internships_count else 0
    }
