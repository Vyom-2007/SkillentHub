import bcrypt
from app.database.connection import get_db_connection


def find_user_by_email(email):
    """Return user dict or None."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            return cur.fetchone()
    finally:
        conn.close()


def create_user(full_name, email, password):
    """Hash password with bcrypt and insert a new user. Returns user_id."""
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (full_name, email, password_hash) VALUES (%s, %s, %s)",
                (full_name, email, hashed.decode('utf-8')),
            )
            return cur.lastrowid
    finally:
        conn.close()


def verify_password(plain_password, hashed_password):
    """Check a plain-text password against a bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8'),
    )


def update_password(user_id, new_password):
    """Hash and store a new password for the given user."""
    hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET password_hash = %s WHERE user_id = %s",
                (hashed.decode('utf-8'), user_id),
            )
    finally:
        conn.close()


def update_last_login(user_id):
    """Set last_login to the current timestamp."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET last_login = NOW() WHERE user_id = %s",
                (user_id,),
            )
    finally:
        conn.close()
