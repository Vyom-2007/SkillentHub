"""
Event service.
Handles competitions and hackathons browsing, details, and registration.
"""
from app.database.connection import execute_query, execute_insert, get_db_connection
from datetime import datetime


def get_event_status(start_date, end_date):
    """Calculate event status based on current time."""
    now = datetime.now()
    
    # Convert strings to datetime if needed
    if isinstance(start_date, str):
        try:
            start_date = datetime.fromisoformat(start_date)
        except ValueError:
            pass
            
    if isinstance(end_date, str):
        try:
            end_date = datetime.fromisoformat(end_date)
        except ValueError:
            pass
            
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
    try:
        reg_id = execute_insert(query, (competition_id, user_id))
        if reg_id:
            return True, reg_id
    except Exception as e:
        return False, f"Database error: {str(e)}"
        
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



def register_hackathon(hackathon_id, user_id, team_name=None, members=None):
    """Register user (and team) for a hackathon."""
    from app.services import team_service, auth_service
    
    # Check if already registered
    if is_registered_hackathon(hackathon_id, user_id):
        return False, "You are already registered"
    
    # Check hackathon exists and is open
    hack = get_hackathon_by_id(hackathon_id)
    if not hack:
        return False, "Hackathon not found"
    
    if hack['status'] == 'completed':
        return False, "Registration closed"
    
    # If members provided, validate and handle team
    team_id = None
    member_ids = []
    
    if members:
        if not team_name:
            return False, "Team name is required when adding members"
            
        # Validate team size
        max_size = hack.get('team_size', 1) # Fallback to 1 if null (though schema says int, might be null)
        # Check team_size logic. Schema has team_size? 
        # Wait, previous view of schema for hackathons: `team_size` int DEFAULT NULL.
        # So we should check that.
        
        current_size = 1 + len(members) # Leader + members
        if max_size and current_size > max_size:
             return False, f"Team size exceeds limit of {max_size}"

        # Resolve emails to User IDs
        for email in members:
            user = auth_service.get_user_by_email(email)
            if not user:
                return False, f"User with email {email} not found"
            
            m_id = user['user_id']
            if m_id == user_id:
                return False, "You cannot add yourself as a member"
                
            if is_registered_hackathon(hackathon_id, m_id):
                return False, f"User {email} is already registered"
                
            if m_id in member_ids:
                return False, f"Duplicate member email: {email}"
                
            member_ids.append(m_id)
            
        # Create Team
        # We use a direct DB transaction here to ensure atomicity of team + registrations
        # instead of calling team_service which might commit separately.
        # But for simplicity let's use team_service to create the team shell 
        # and then manually add members and registrations in a transaction.
        # Actually, let's just do it all here in one transaction.
        
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 1. Create Team if needed
            if team_name and (members or (hack.get('team_size') or 1) > 1):
                # Check if team already exists for this user/event? 
                # team_service logic handles user-event uniqueness for teams.
                # Let's insert directly.
                cursor.execute("""
                    INSERT INTO teams (team_name, item_type, item_id, created_by, max_members)
                    VALUES (%s, 'hackathon', %s, %s, %s)
                """, (team_name, hackathon_id, user_id, hack.get('team_size')))
                team_id = cursor.lastrowid
                
                # Add leader
                cursor.execute("INSERT INTO team_members (team_id, user_id, role) VALUES (%s, %s, 'leader')", (team_id, user_id))
                
                # Add members
                for m_id in member_ids:
                     cursor.execute("INSERT INTO team_members (team_id, user_id, role) VALUES (%s, %s, 'member')", (team_id, m_id))
            
            # 2. Register Leader
            cursor.execute("""
                INSERT INTO hackathon_registrations (hackathon_id, user_id, team_name) 
                VALUES (%s, %s, %s)
            """, (hackathon_id, user_id, team_name))
            
            # 3. Register Members
            for m_id in member_ids:
                cursor.execute("""
                    INSERT INTO hackathon_registrations (hackathon_id, user_id, team_name) 
                    VALUES (%s, %s, %s)
                """, (hackathon_id, m_id, team_name))
                
        connection.commit()
        return True, "Registration successful"
        
    except Exception as e:
        connection.rollback()
        return False, f"Database error: {str(e)}"
    # finally:
    #     connection.close() # Do not close shared connection managed by Flask g


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
