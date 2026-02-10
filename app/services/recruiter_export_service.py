"""
Recruiter Export Service.
Handles fetching event registrations and generating CSV files.
"""
import csv
import io
from app.database.connection import execute_query

def get_event_registrations(item_type, item_id, recruiter_id):
    """
    Fetch registrations for a specific event (competition/hackathon).
    Verifies that the event belongs to the recruiter.
    """
    # 1. Verify Ownership
    table_map = {'competition': 'competitions', 'hackathon': 'hackathons'}
    id_col_map = {'competition': 'competition_id', 'hackathon': 'hackathon_id'}
    
    if item_type not in table_map:
        return None
        
    table = table_map[item_type]
    id_col = id_col_map[item_type]
    
    check_sql = f"SELECT title FROM {table} WHERE {id_col} = %s AND recruiter_id = %s"
    event = execute_query(check_sql, (item_id, recruiter_id), fetch_one=True)
    
    if not event:
        return None # Not found or access denied
        
    # 2. Fetch Registrations
    # Registrations are in 'applications' table with item_type and item_id
    sql = """
        SELECT 
            a.application_id, a.applied_at,
            CONCAT(u.first_name, ' ', u.last_name) as candidate_name,
            u.email,
            p.phone_number,
            p.user_id
        FROM applications a
        JOIN users u ON a.user_id = u.user_id
        LEFT JOIN profiles p ON u.user_id = p.user_id
        WHERE a.item_type = %s AND a.item_id = %s
        ORDER BY a.applied_at DESC
    """
    registrations = execute_query(sql, (item_type, item_id))
    
    return {
        'event_title': event['title'],
        'registrations': registrations
    }

def generate_registrations_csv(registrations, event_title):
    """
    Generate CSV string from registrations list.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['Candidate Name', 'Email', 'Phone', 'Registration Date'])
    
    # Rows
    for reg in registrations:
        writer.writerow([
            reg['candidate_name'],
            reg['email'],
            reg['phone_number'] or 'N/A',
            reg['applied_at'].strftime('%Y-%m-%d %H:%M:%S') if reg['applied_at'] else 'N/A'
        ])
        
    return output.getvalue()
