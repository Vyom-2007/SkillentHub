
"""
Recruiter Settings Service.
Handles profile updates and password changes for recruiters.
"""
from app.database.connection import execute_query, execute_update
from app.services import recruiter_auth_service
import re

def get_profile(recruiter_id):
    """
    Fetch recruiter profile details.
    """
    query = "SELECT company_name, company_email, created_at FROM recruiters WHERE recruiter_id = %s"
    return execute_query(query, (recruiter_id,), fetch_one=True)

def update_profile(recruiter_id, company_name):
    """
    Update recruiter profile (company name).
    """
    query = "UPDATE recruiters SET company_name = %s WHERE recruiter_id = %s"
    return execute_update(query, (company_name, recruiter_id)) > 0

def validate_password_complexity(password):
    """
    Validate password complexity.
    Must be at least 8 chars, contain 1 uppercase, 1 number.
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number."
        
    return True, "Valid"

def change_password(recruiter_id, current_password, new_password):
    """
    Change recruiter password.
    """
    # 1. Verify current
    if not recruiter_auth_service.verify_recruiter_by_id(recruiter_id, current_password):
        return False, "Incorrect current password."
        
    # 2. Validate new complexity
    valid, msg = validate_password_complexity(new_password)
    if not valid:
        return False, msg
        
    # 3. Update via auth service
    recruiter_auth_service.update_password(recruiter_id, new_password)
    
    return True, "Password updated successfully."
