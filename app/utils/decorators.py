from functools import wraps
from flask import session, redirect, url_for, flash

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def recruiter_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'recruiter_id' not in session:
            return redirect(url_for('recruiter_auth.login'))
        return f(*args, **kwargs)
    return decorated_function
