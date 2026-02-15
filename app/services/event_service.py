"""
Event service.
Handles competitions and hackathons browsing, details, and registration.
"""
from app.database.connection import execute_query, execute_insert, execute_update, get_db_connection
from datetime import datetime


def get_event_status(start_date, end_date):
    """Calculate event status based on current time."""
    now = datetime.now()
    
    # Convert strings to datetime if needed
    # Convert strings to datetime if needed
    if isinstance(start_date, str):
        try:
            start_date = datetime.fromisoformat(start_date)
        except ValueError:
            # Try common SQL format
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                pass
            
    if isinstance(end_date, str):
        try:
            end_date = datetime.fromisoformat(end_date)
        except ValueError:
            # Try common SQL format
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                pass
    
    if not isinstance(start_date, datetime) or not isinstance(end_date, datetime):
        return 'unknown'
            
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
    
    if comp.get('registration_deadline') and datetime.now() > comp.get('registration_deadline'):
         return False, f"Registration closed on {comp['registration_deadline'].strftime('%b %d, %Y %I:%M %p')}"
    
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

    if hack.get('registration_deadline') and datetime.now() > hack.get('registration_deadline'):
         return False, f"Registration closed on {hack['registration_deadline'].strftime('%b %d, %Y %I:%M %p')}"
    
    # If members provided, validate and handle team
    team_id = None
    member_data = [] # List of dicts: {user_id, name, email}
    
    if team_name or members:
        if not team_name:
            return False, "Team name is required for team registration"
            
        if not members:
             return False, "At least one team member is required for team registration"

        # Validate team size
        max_size = hack.get('team_size_max') or hack.get('team_size') or 1
        min_size = hack.get('team_size_min') or 1
        
        current_size = 1 + len(members) # Leader + members
        
        if max_size and current_size > max_size:
             return False, f"Team size exceeds limit of {max_size}"
             
        if current_size < min_size:
             return False, f"Team size must be at least {min_size} members"

        # Resolve emails to User IDs or keep as non-users
        processed_emails = set()
        
        for m in members:
            # Handle both string (old format) and dict (new format) for backward compatibility/robustness
            if isinstance(m, str):
                email = m
                name = None
            else:
                email = m.get('email')
                name = m.get('name')
            
            if not email:
                continue
                
            if email in processed_emails:
                return False, f"Duplicate member email: {email}"
            processed_emails.add(email)

            # Check if user exists
            user = auth_service.get_user_by_email(email)
            
            if user:
                m_id = user['user_id']
                if m_id == user_id:
                    return False, "You cannot add yourself as a member"
                    
                if is_registered_hackathon(hackathon_id, m_id):
                    return False, f"User {email} is already registered"
                
                # Get name from profile if not provided
                if not name:
                    profile = auth_service.get_user_profile(m_id)
                    name = profile.get('full_name') if profile else 'Unknown'
                    
                member_data.append({
                    'user_id': m_id,
                    'name': name,
                    'email': email
                })
            else:
                # Non-user member - REJECT
                return False, f"User with email {email} is not registered. All team members must be registered users."
            
        # Create Team & Register
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 1. Create Team if needed
            if team_name and (members or (hack.get('team_size') or 1) > 1):
                cursor.execute("""
                    INSERT INTO teams (team_name, item_type, item_id, created_by, max_members)
                    VALUES (%s, 'hackathon', %s, %s, %s)
                """, (team_name, hackathon_id, user_id, hack.get('team_size')))
                team_id = cursor.lastrowid
                
                # Add leader
                # Fetch leader name/email for completeness? 
                leader_profile = auth_service.get_user_profile(user_id)
                leader_name = leader_profile.get('full_name') if leader_profile else 'Leader'
                leader_user = auth_service.get_user_by_id(user_id)
                leader_email = leader_user.get('email') if leader_user else ''

                cursor.execute("""
                    INSERT INTO team_members (team_id, user_id, name, email, role) 
                    VALUES (%s, %s, %s, %s, 'leader')
                """, (team_id, user_id, leader_name, leader_email))
                
                # Add members
                for member in member_data:
                     cursor.execute("""
                        INSERT INTO team_members (team_id, user_id, name, email, role) 
                        VALUES (%s, %s, %s, %s, 'member')
                     """, (team_id, member['user_id'], member['name'], member['email']))
            
            # 2. Register Leader
            cursor.execute("""
                INSERT INTO hackathon_registrations (hackathon_id, user_id, team_name) 
                VALUES (%s, %s, %s)
            """, (hackathon_id, user_id, team_name))
            
            # 3. Register Members
            for member in member_data:
                cursor.execute("""
                    INSERT INTO hackathon_registrations (hackathon_id, user_id, name, email, team_name) 
                    VALUES (%s, %s, %s, %s, %s)
                """, (hackathon_id, member['user_id'], member['name'], member['email'], team_name))
                
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
                cr.registered_at,
                t.team_id,
                t.created_by as team_leader_id
            FROM competition_registrations cr
            JOIN competitions c ON cr.competition_id = c.competition_id
            LEFT JOIN recruiters r ON c.recruiter_id = r.recruiter_id
            LEFT JOIN teams t ON t.item_type = 'competition' AND t.item_id = c.competition_id 
                AND t.team_id IN (SELECT team_id FROM team_members WHERE user_id = %s)
            WHERE cr.user_id = %s
            ORDER BY c.start_date ASC
        """
        comps = execute_query(comp_query, (user_id, user_id), fetch_all=True) or []
        for c in comps:
            c['status'] = get_event_status(c['start_date'], c['end_date'])
            c['is_leader'] = (c['team_leader_id'] == int(user_id)) if c.get('team_leader_id') else False
        results.extend(comps)
    
    # Get hackathon registrations
    if event_type in [None, 'hackathon']:
        hack_query = """
            SELECT 
                'hackathon' as event_type,
                h.hackathon_id as event_id,
                h.title, h.description, h.start_date, h.end_date, h.venue, h.mode, h.prizes,
                r.company_name,
                hr.registered_at, hr.team_name,
                t.team_id,
                t.created_by as team_leader_id
            FROM hackathon_registrations hr
            JOIN hackathons h ON hr.hackathon_id = h.hackathon_id
            LEFT JOIN recruiters r ON h.recruiter_id = r.recruiter_id
            LEFT JOIN teams t ON t.item_type = 'hackathon' AND t.item_id = h.hackathon_id
                AND t.team_id IN (SELECT team_id FROM team_members WHERE user_id = %s)
            WHERE hr.user_id = %s
            ORDER BY h.start_date ASC
        """
        hacks = execute_query(hack_query, (user_id, user_id), fetch_all=True) or []
        for h in hacks:
            h['status'] = get_event_status(h['start_date'], h['end_date'])
            h['is_leader'] = (h['team_leader_id'] == int(user_id)) if h.get('team_leader_id') else False
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


def unregister_from_event(user_id, event_type, event_id):
    """
    Unregister a user from an event.
    Handles both individual and team registrations.
    """
    from app.services import team_service
    
    # 1. Check if user has a team for this event
    # We can query the teams table directly or use team_service
    # But event_service shouldn't depend circularly on team_service if possible.
    # Actually team_service is imported inside functions usually.
    
    # Let's find the team first
    team = team_service.get_user_team_for_event(user_id, event_type, event_id)
    
    if team:
        # User is in a team
        if team['created_by'] == user_id:
            # User is Leader -> Cancel entire team registration
            # This should ideally cascade deletion of team members' registrations too
            return team_service.unregister_team(user_id, team['team_id'])
        else:
            # User is Member -> Leave team
            # This should remove them from the team and thus the event
            return team_service.leave_team(user_id, team['team_id'])
            
    # 2. User is NOT in a team (Individual Registration)
    # Just delete the registration record
    
    table = 'competition_registrations' if event_type == 'competition' else 'hackathon_registrations'
    id_col = 'competition_id' if event_type == 'competition' else 'hackathon_id'
    
    query = f"DELETE FROM {table} WHERE {id_col} = %s AND user_id = %s"
    rows = execute_update(query, (event_id, user_id))
    
    if rows > 0:
        return True, "Registration cancelled successfully"
    return False, "You were not registered for this event"
