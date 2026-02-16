from app.database.connection import execute_query
from app.services import connection_service, application_service

def can_access_resume(filename, viewer_id, viewer_role='user'):
    """
    Check if a user/recruiter can access a specific resume file.
    
    Args:
        filename (str): The filename of the resume (e.g., resume_123.pdf)
        viewer_id (int): ID of the user or recruiter trying to access
        viewer_role (str): 'user' or 'recruiter'
        
    Returns:
        bool: True if access allowed, False otherwise
    """
    if not filename:
        return False
        
    # 1. Identify the owner of the resume
    # Check profiles first
    query = "SELECT user_id, visibility, show_resume FROM profiles WHERE resume_path LIKE %s"
    # Note: Using LIKE because path might be full path or just filename. 
    # Usually we store just filename in 'resume_path' column? Let's check schema/service.
    # application_service.save_resume returns just filename. profile service stores what?
    # Profile service update: matches filename.
    
    owner = execute_query(query, (f"%{filename}",), fetch_one=True)
    
    # If not found in profiles, check applications
    if not owner:
        app_query = "SELECT application_id, user_id, item_type, item_id FROM applications WHERE resume_path LIKE %s"
        app_data = execute_query(app_query, (f"%{filename}",), fetch_one=True)
        
        if not app_data:
            return False # File not linked to anyone known
            
        owner_id = app_data['user_id']
        
        # Owner always has access
        if viewer_role == 'user' and owner_id == viewer_id:
            return True
            
        # Recruiter access: Check if they are the recipient
        if viewer_role == 'recruiter':
            rec_check = """
                SELECT 1 
                FROM jobs j 
                WHERE j.job_id = %s AND j.recruiter_id = %s
                UNION
                SELECT 1
                FROM internships i
                WHERE i.internship_id = %s AND i.recruiter_id = %s
            """
            # item_id is job_id or internship_id
            # item_type is 'job' or 'internship'
            is_recipient = False
            if app_data['item_type'] == 'job':
                 is_recipient = execute_query("SELECT 1 FROM jobs WHERE job_id=%s AND recruiter_id=%s", (app_data['item_id'], viewer_id), fetch_one=True)
            elif app_data['item_type'] == 'internship':
                 is_recipient = execute_query("SELECT 1 FROM internships WHERE internship_id=%s AND recruiter_id=%s", (app_data['item_id'], viewer_id), fetch_one=True)
                 
            return bool(is_recipient)
            
        return False

    else:
        # It IS a profile resume
        owner_id = owner['user_id']
        visibility = owner.get('visibility', 'public')
        show_resume = owner.get('show_resume', 0)
        
        # Owner always has access
        if viewer_role == 'user' and owner_id == viewer_id:
            return True
        
        # Recruiter access
        if viewer_role == 'recruiter':
            return True
            
        # Other Users
        if viewer_role == 'user':
            if not show_resume:
                return False
            if visibility == 'private':
                return connection_service.are_connected(viewer_id, owner_id)
            return True
            
    return False
