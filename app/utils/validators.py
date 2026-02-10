import re

def validate_registration(email, password, full_name):
    errors = []
    
    if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        errors.append("Invalid email address.")
        
    if not password or len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    elif not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter.")
    elif not re.search(r"[0-9]", password):
        errors.append("Password must contain at least one number.")
        
    if not full_name or len(full_name.strip()) < 2:
        errors.append("Full name is required.")
        
    return errors

def validate_login(email, password):
    errors = []
    if not email:
        errors.append("Email is required.")
    if not password:
        errors.append("Password is required.")
    return errors
