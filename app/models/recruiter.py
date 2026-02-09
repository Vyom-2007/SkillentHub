"""
Recruiter model.
Handles recruiter data operations using raw SQL.
"""
from app.database.connection import execute_query, execute_insert


def create(company_name, email, password_hash):
    """Create a new recruiter."""
    query = """
        INSERT INTO recruiters (company_name, company_email, password_hash)
        VALUES (%s, %s, %s)
    """
    try:
        recruiter_id = execute_insert(query, (company_name, email, password_hash))
        return recruiter_id, None
    except Exception as e:
        if 'Duplicate' in str(e):
            return None, "Email already registered"
        return None, str(e)


def get_by_email(email):
    """Get recruiter by email."""
    query = """
        SELECT recruiter_id, company_name, company_email, password_hash, 
               created_at, is_active
        FROM recruiters 
        WHERE company_email = %s
    """
    return execute_query(query, (email,), fetch_one=True)


def get_by_id(recruiter_id):
    """Get recruiter by ID."""
    query = """
        SELECT recruiter_id, company_name, company_email, password_hash, 
               created_at, is_active
        FROM recruiters 
        WHERE recruiter_id = %s
    """
    return execute_query(query, (recruiter_id,), fetch_one=True)


def email_exists(email):
    """Check if email is already registered."""
    query = "SELECT 1 FROM recruiters WHERE company_email = %s"
    result = execute_query(query, (email,), fetch_one=True)
    return result is not None


def update_password(recruiter_id, password_hash):
    """Update recruiter password."""
    from app.database.connection import execute_update
    query = "UPDATE recruiters SET password_hash = %s WHERE recruiter_id = %s"
    return execute_update(query, (password_hash, recruiter_id))
