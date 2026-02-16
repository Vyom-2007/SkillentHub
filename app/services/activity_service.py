"""
Activity Service
Handles logging and retrieving activity feed items.
"""
from app.database.connection import execute_insert, execute_query
import json

def log_activity(action_type, details=None, user_id=None, recruiter_id=None, item_type=None, item_id=None):
    """
    Log an activity.
    
    Args:
        action_type (str): Type of action (e.g., 'job_posted', 'user_hired', 'team_created', 'connection_made')
        details (str/dict): Additional details. If dict, will be JSON encoded.
        user_id (int): ID of user performing the action (optional)
        recruiter_id (int): ID of recruiter performing the action (optional)
        item_type (str): Type of related item (e.g., 'job', 'application', 'team')
        item_id (int): ID of related item (optional)
    """
    if isinstance(details, dict):
        details = json.dumps(details)
        
    query = """
        INSERT INTO activity_logs 
        (user_id, recruiter_id, action_type, item_type, item_id, details)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    execute_insert(query, (user_id, recruiter_id, action_type, item_type, item_id, details))


def get_activity_feed(page=1, per_page=20, filter_type=None):
    """
    Get paginated activity feed.
    
    Args:
        page (int): Page number
        per_page (int): Items per page
        filter_type (str): Optional filter by action_type category ('jobs', 'community')
    """
    offset = (page - 1) * per_page
    params = []
    where_clause = ""
    
    if filter_type == 'jobs':
        where_clause = "WHERE action_type IN ('job_posted', 'internship_posted', 'hackathon_posted', 'competition_posted')"
    elif filter_type == 'community':
        where_clause = "WHERE action_type IN ('team_created', 'connection_made', 'user_hired')"
        
    query = f"""
        SELECT 
            al.*,
            -- Actor details
            CASE 
                WHEN al.recruiter_id IS NOT NULL THEN r.company_name
                WHEN al.user_id IS NOT NULL THEN p_actor.full_name
            END as actor_name,
            CASE 
                WHEN al.user_id IS NOT NULL THEN p_actor.profile_picture
            END as actor_picture,
            
            -- Target user details (for connection_made, user_hired etc)
            -- Note: details usually contains target info, but we can try to join if item_type='payment' etc.
            -- For simplicity, we rely on 'details' column for complex text generation in UI or minimal structure here.
            
            -- Timestamps
            al.created_at
            
        FROM activity_logs al
        LEFT JOIN recruiters r ON al.recruiter_id = r.recruiter_id
        LEFT JOIN profiles p_actor ON al.user_id = p_actor.user_id
        {where_clause}
        ORDER BY al.created_at DESC
        LIMIT %s OFFSET %s
    """
    params.extend([per_page, offset])
    
    activities = execute_query(query, tuple(params), fetch_all=True) or []
    
    # Post-process to parse details if JSON
    for activity in activities:
        try:
            if activity['details'] and (activity['details'].startswith('{') or activity['details'].startswith('[')):
                activity['details'] = json.loads(activity['details'])
        except:
            pass
            
    return activities
