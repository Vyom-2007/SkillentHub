"""
Network service.
Handles user search and filtering with dynamic SQL.
"""
from app.database.connection import execute_query


def get_all_users(page=1, per_page=50, current_user_id=None):
    """Get all users with pagination, excluding current user."""
    offset = (page - 1) * per_page
    
    query = """
        SELECT 
            u.user_id, u.email,
            p.full_name, p.headline, p.profile_picture, p.location,
            (SELECT GROUP_CONCAT(s.skill_name ORDER BY s.skill_name SEPARATOR ', ')
             FROM user_skills us
             JOIN skills s ON us.skill_id = s.skill_id
             WHERE us.user_id = u.user_id
             LIMIT 3) as top_skills
        FROM users u
        LEFT JOIN profiles p ON u.user_id = p.user_id
        WHERE u.is_active = 1 AND p.profile_id IS NOT NULL
        AND u.user_id != %s
        AND u.email NOT IN (SELECT company_email FROM recruiters)
        ORDER BY p.full_name ASC
        LIMIT %s OFFSET %s
    """
    
    users = execute_query(query, (current_user_id or 0, per_page, offset), fetch_all=True)
    
    # Get total count
    count_result = execute_query(
        "SELECT COUNT(*) as total FROM users u JOIN profiles p ON u.user_id = p.user_id WHERE u.is_active = 1 AND u.email NOT IN (SELECT company_email FROM recruiters)",
        fetch_one=True
    )
    total = count_result['total'] if count_result else 0
    
    return {
        'users': users or [],
        'total': total,
        'page': page,
        'per_page': per_page,
        'has_more': offset + per_page < total
    }


def search_users(q=None, skills=None, location=None, page=1, per_page=50, current_user_id=None):
    """
    Search users with dynamic SQL filtering.
    
    Args:
        q: Search query for name/headline
        skills: Comma-separated skill names (user must have ALL - AND logic)
        location: Location filter
        page: Page number
        per_page: Results per page
    """
    offset = (page - 1) * per_page
    params = []
    where_clauses = ["u.is_active = 1", "p.profile_id IS NOT NULL", "u.email NOT IN (SELECT company_email FROM recruiters)"]
    join_clauses = ["LEFT JOIN profiles p ON u.user_id = p.user_id"]
    
    # Exclude current user
    if current_user_id:
        where_clauses.append("u.user_id != %s")
        params.append(current_user_id)
    
    # Name/Headline search
    if q and q.strip():
        search_term = f"%{q.strip()}%"
        where_clauses.append("(p.full_name LIKE %s OR p.headline LIKE %s)")
        params.extend([search_term, search_term])
    
    # Location filter
    if location and location.strip():
        where_clauses.append("p.location LIKE %s")
        params.append(f"%{location.strip()}%")
    
    # Skills filter (AND logic - user must have ALL selected skills)
    skill_list = []
    if skills and skills.strip():
        skill_list = [s.strip() for s in skills.split(',') if s.strip()]
    
    if skill_list:
        # Join with user_skills and skills tables
        join_clauses.append("JOIN user_skills us ON u.user_id = us.user_id")
        join_clauses.append("JOIN skills sk ON us.skill_id = sk.skill_id")
        
        # Filter for matching skills
        placeholders = ', '.join(['%s'] * len(skill_list))
        where_clauses.append(f"sk.skill_name IN ({placeholders})")
        params.extend(skill_list)
        
        # Group and filter for users having ALL selected skills
        group_clause = "GROUP BY u.user_id"
        having_clause = f"HAVING COUNT(DISTINCT sk.skill_id) = {len(skill_list)}"
    else:
        group_clause = ""
        having_clause = ""
    
    # Build main query
    query = f"""
        SELECT 
            u.user_id, u.email,
            p.full_name, p.headline, p.profile_picture, p.location
        FROM users u
        {' '.join(join_clauses)}
        WHERE {' AND '.join(where_clauses)}
        {group_clause}
        {having_clause}
        ORDER BY p.full_name ASC
        LIMIT %s OFFSET %s
    """
    params.extend([per_page, offset])
    
    users = execute_query(query, tuple(params), fetch_all=True) or []
    
    # Get skills for each user
    for user in users:
        user['skills'] = get_user_skills(user['user_id'], limit=3)
    
    # Count query (same filters but no limit/offset)
    count_params = params[:-2]  # Remove limit/offset params
    count_query = f"""
        SELECT COUNT(DISTINCT u.user_id) as total
        FROM users u
        {' '.join(join_clauses)}
        WHERE {' AND '.join(where_clauses)}
    """
    
    count_result = execute_query(count_query, tuple(count_params), fetch_one=True)
    total = count_result['total'] if count_result else 0
    
    return {
        'users': users,
        'total': total,
        'page': page,
        'per_page': per_page,
        'has_more': offset + per_page < total
    }


def get_user_skills(user_id, limit=3):
    """Get skills for a user."""
    query = """
        SELECT s.skill_id, s.skill_name
        FROM user_skills us
        JOIN skills s ON us.skill_id = s.skill_id
        WHERE us.user_id = %s
        ORDER BY s.skill_name
        LIMIT %s
    """
    return execute_query(query, (user_id, limit), fetch_all=True) or []


def get_all_locations():
    """Get all unique locations from profiles."""
    query = """
        SELECT DISTINCT location 
        FROM profiles 
        WHERE location IS NOT NULL AND location != ''
        ORDER BY location
    """
    results = execute_query(query, fetch_all=True) or []
    return [r['location'] for r in results]


def get_all_skills():
    """Get all skills for the filter dropdown."""
    query = "SELECT skill_id, skill_name FROM skills ORDER BY skill_name"
    return execute_query(query, fetch_all=True) or []
