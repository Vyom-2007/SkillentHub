"""
Event service.
Handles competitions and hackathons browsing, details, and registration.
"""
from app.database.connection import execute_query, execute_insert, get_db_connection
from datetime import datetime


def get_event_status(start_date, end_date):
    """Calculate event status based on current time."""
    now = datetime.now()
    if now < start_date:
        return 'upcoming'
    elif start_date <= now <= end_date:
        return 'ongoing'
    else:
        return 'completed'


# ========== COMPETITIONS ==========

def get_competitions(page=1, per_page=50):
    """Get all active competitions sorted by start date."""
    offset = (page - 1) * per_page
    
    query = """
        SELECT 
            c.*,
            r.company_name,
            (SELECT COUNT(*) FROM competition_registrations WHERE competition_id = c.competition_id) as registration_count
        FROM competitions c
        LEFT JOIN recruiters r ON c.recruiter_id = r.recruiter_id
        WHERE c.is_active = 1
        ORDER BY c.start_date ASC
        LIMIT %s OFFSET %s
    """
    competitions = execute_query(query, (per_page, offset), fetch_all=True) or []
    
    # Add status to each competition
    for comp in competitions:
        comp['status'] = get_event_status(comp['start_date'], comp['end_date'])
    
    return competitions


def get_competition_by_id(competition_id):
    """Get competition details by ID."""
    query = """
        SELECT 
            c.*,
            r.company_name, r.company_email,
            (SELECT COUNT(*) FROM competition_registrations WHERE competition_id = c.competition_id) as registration_count
        FROM competitions c
        LEFT JOIN recruiters r ON c.recruiter_id = r.recruiter_id
        WHERE c.competition_id = %s
    """
    comp = execute_query(query, (competition_id,), fetch_one=True)
    if comp:
        comp['status'] = get_event_status(comp['start_date'], comp['end_date'])
    return comp


def is_registered_competition(competition_id, user_id):
    """Check if user is registered for a competition."""
    query = "SELECT registration_id FROM competition_registrations WHERE competition_id = %s AND user_id = %s"
    result = execute_query(query, (competition_id, user_id), fetch_one=True)
    return result is not None


def register_competition(competition_id, user_id):
    """Register user for a competition."""
    # Check if already registered
    if is_registered_competition(competition_id, user_id):
        return False, "Already registered"
    
    # Check competition exists and is open
    comp = get_competition_by_id(competition_id)
    if not comp:
        return False, "Competition not found"
    
    if comp['status'] == 'completed':
        return False, "Registration closed"
    
    if comp['max_participants'] and comp['registration_count'] >= comp['max_participants']:
        return False, "Maximum participants reached"
    
    # Register
    query = "INSERT INTO competition_registrations (competition_id, user_id) VALUES (%s, %s)"
    reg_id = execute_insert(query, (competition_id, user_id))
    
    if reg_id:
        return True, reg_id
    return False, "Registration failed"


# ========== HACKATHONS ==========

def get_hackathons(page=1, per_page=50):
    """Get all active hackathons sorted by start date."""
    offset = (page - 1) * per_page
    
    query = """
        SELECT 
            h.*,
            r.company_name,
            (SELECT COUNT(*) FROM hackathon_registrations WHERE hackathon_id = h.hackathon_id) as registration_count
        FROM hackathons h
        LEFT JOIN recruiters r ON h.recruiter_id = r.recruiter_id
        WHERE h.is_active = 1
        ORDER BY h.start_date ASC
        LIMIT %s OFFSET %s
    """
    hackathons = execute_query(query, (per_page, offset), fetch_all=True) or []
    
    # Add status to each hackathon
    for hack in hackathons:
        hack['status'] = get_event_status(hack['start_date'], hack['end_date'])
    
    return hackathons


def get_hackathon_by_id(hackathon_id):
    """Get hackathon details by ID."""
    query = """
        SELECT 
            h.*,
            r.company_name, r.company_email,
            (SELECT COUNT(*) FROM hackathon_registrations WHERE hackathon_id = h.hackathon_id) as registration_count
        FROM hackathons h
        LEFT JOIN recruiters r ON h.recruiter_id = r.recruiter_id
        WHERE h.hackathon_id = %s
    """
    hack = execute_query(query, (hackathon_id,), fetch_one=True)
    if hack:
        hack['status'] = get_event_status(hack['start_date'], hack['end_date'])
    return hack


def is_registered_hackathon(hackathon_id, user_id):
    """Check if user is registered for a hackathon."""
    query = "SELECT registration_id FROM hackathon_registrations WHERE hackathon_id = %s AND user_id = %s"
    result = execute_query(query, (hackathon_id, user_id), fetch_one=True)
    return result is not None


def register_hackathon(hackathon_id, user_id, team_name=None):
    """Register user for a hackathon."""
    # Check if already registered
    if is_registered_hackathon(hackathon_id, user_id):
        return False, "Already registered"
    
    # Check hackathon exists and is open
    hack = get_hackathon_by_id(hackathon_id)
    if not hack:
        return False, "Hackathon not found"
    
    if hack['status'] == 'completed':
        return False, "Registration closed"
    
    # Register
    query = "INSERT INTO hackathon_registrations (hackathon_id, user_id, team_name) VALUES (%s, %s, %s)"
    reg_id = execute_insert(query, (hackathon_id, user_id, team_name))
    
    if reg_id:
        return True, reg_id
    return False, "Registration failed"


# ========== USER REGISTRATIONS ==========

def get_user_registrations(user_id, event_type=None):
    """Get all registrations for a user."""
    results = []
    
    # Get competition registrations
    if event_type in [None, 'competition']:
        comp_query = """
            SELECT 
                'competition' as event_type,
                c.competition_id as event_id,
                c.title, c.description, c.start_date, c.end_date, c.prize,
                r.company_name,
                cr.registered_at
            FROM competition_registrations cr
            JOIN competitions c ON cr.competition_id = c.competition_id
            LEFT JOIN recruiters r ON c.recruiter_id = r.recruiter_id
            WHERE cr.user_id = %s
            ORDER BY c.start_date ASC
        """
        comps = execute_query(comp_query, (user_id,), fetch_all=True) or []
        for c in comps:
            c['status'] = get_event_status(c['start_date'], c['end_date'])
        results.extend(comps)
    
    # Get hackathon registrations
    if event_type in [None, 'hackathon']:
        hack_query = """
            SELECT 
                'hackathon' as event_type,
                h.hackathon_id as event_id,
                h.title, h.description, h.start_date, h.end_date, h.venue, h.mode, h.prizes,
                r.company_name,
                hr.registered_at, hr.team_name
            FROM hackathon_registrations hr
            JOIN hackathons h ON hr.hackathon_id = h.hackathon_id
            LEFT JOIN recruiters r ON h.recruiter_id = r.recruiter_id
            WHERE hr.user_id = %s
            ORDER BY h.start_date ASC
        """
        hacks = execute_query(hack_query, (user_id,), fetch_all=True) or []
        for h in hacks:
            h['status'] = get_event_status(h['start_date'], h['end_date'])
        results.extend(hacks)
    
    # Sort by start date
    results.sort(key=lambda x: x['start_date'])
    return results


def get_event_counts():
    """Get counts of active events."""
    comp_count = execute_query(
        "SELECT COUNT(*) as count FROM competitions WHERE is_active = 1",
        fetch_one=True
    )
    hack_count = execute_query(
        "SELECT COUNT(*) as count FROM hackathons WHERE is_active = 1",
        fetch_one=True
    )
    return {
        'competitions': comp_count['count'] if comp_count else 0,
        'hackathons': hack_count['count'] if hack_count else 0
    }
