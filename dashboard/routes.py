"""
Dashboard routes blueprint for user dashboard and activity overview.
"""

from functools import wraps

from flask import Blueprint, render_template, redirect, url_for, flash, session
from database.db import execute_query


# Create the dashboard blueprint
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


def login_required(f):
    """Decorator to require user login for protected routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@dashboard_bp.route('/')
@login_required
def index():
    """
    Dashboard home route displaying user stats and recent activity.
    """
    user_id = session['user_id']
    
    # ===== FETCH COUNTS FOR BADGES =====
    
    # Unread notifications count
    unread_notifs = execute_query(
        "SELECT COUNT(*) as count FROM notifications WHERE user_id = %s AND is_read = FALSE",
        (user_id,),
        fetch_one=True
    )
    
    # Pending connection requests count
    pending_requests = execute_query(
        "SELECT COUNT(*) as count FROM connections WHERE receiver_id = %s AND status = 'pending'",
        (user_id,),
        fetch_one=True
    )
    
    # Unread messages count (messages where user is receiver)
    unread_messages = execute_query(
        "SELECT COUNT(*) as count FROM messages WHERE receiver_id = %s",
        (user_id,),
        fetch_one=True
    )
    
    # Total connections count
    total_connections = execute_query(
        """
        SELECT COUNT(*) as count FROM connections 
        WHERE status = 'accepted' AND (sender_id = %s OR receiver_id = %s)
        """,
        (user_id, user_id),
        fetch_one=True
    )
    
    # Total posts count
    total_posts = execute_query(
        "SELECT COUNT(*) as count FROM posts WHERE user_id = %s",
        (user_id,),
        fetch_one=True
    )
    
    # ===== FETCH RECENT ACTIVITY =====
    
    # Recent job applications (top 5)
    my_applications = execute_query(
        """
        SELECT a.id, a.status, a.created_at, 
               o.id as opportunity_id, o.title, o.company
        FROM applications a
        INNER JOIN opportunities o ON a.opportunity_id = o.id
        WHERE a.user_id = %s
        ORDER BY a.created_at DESC
        LIMIT 5
        """,
        (user_id,),
        fetch_all=True
    )
    
    # Upcoming event registrations (top 5)
    my_events = execute_query(
        """
        SELECT e.id, e.title, e.type, e.event_date, e.location, er.created_at as registered_at
        FROM event_registrations er
        INNER JOIN events e ON er.event_id = e.id
        WHERE er.user_id = %s AND e.event_date >= NOW()
        ORDER BY e.event_date ASC
        LIMIT 5
        """,
        (user_id,),
        fetch_all=True
    )
    
    # Recent posts from feed (top 5)
    recent_posts = execute_query(
        """
        SELECT p.id, p.content, p.created_at, u.full_name
        FROM posts p
        INNER JOIN users u ON p.user_id = u.id
        ORDER BY p.created_at DESC
        LIMIT 5
        """,
        fetch_all=True
    )
    
    # Recent notifications (top 5)
    recent_notifications = execute_query(
        """
        SELECT id, message, type, is_read, created_at
        FROM notifications
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 5
        """,
        (user_id,),
        fetch_all=True
    )
    
    # Get user info
    user = execute_query(
        "SELECT id, full_name, profile_pic, bio FROM users WHERE id = %s",
        (user_id,),
        fetch_one=True
    )
    
    return render_template(
        'dashboard/index.html',
        user=user,
        # Counts for badges
        unread_notifs=unread_notifs['count'] if unread_notifs else 0,
        pending_requests=pending_requests['count'] if pending_requests else 0,
        unread_messages=unread_messages['count'] if unread_messages else 0,
        total_connections=total_connections['count'] if total_connections else 0,
        total_posts=total_posts['count'] if total_posts else 0,
        # Recent activity
        my_applications=my_applications or [],
        my_events=my_events or [],
        recent_posts=recent_posts or [],
        recent_notifications=recent_notifications or []
    )
