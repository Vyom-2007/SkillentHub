"""
Events routes blueprint for viewing and registering for events.
"""

from functools import wraps

from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from database.db import execute_query


# Create the events blueprint
events_bp = Blueprint('events', __name__, url_prefix='/events')


def login_required(f):
    """Decorator to require user login for protected routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@events_bp.route('/')
def list_events():
    """
    Display all events ordered by event_date (upcoming first).
    Supports optional filtering by event type via query param.
    """
    event_type = request.args.get('type', '').strip()
    
    if event_type:
        # Filter by type
        events = execute_query(
            """
            SELECT id, title, type, description, event_date, location, 
                   max_participants, created_at 
            FROM events 
            WHERE type = %s
            ORDER BY event_date ASC
            """,
            (event_type,),
            fetch_all=True
        )
    else:
        # Show all events
        events = execute_query(
            """
            SELECT id, title, type, description, event_date, location, 
                   max_participants, created_at 
            FROM events 
            ORDER BY event_date ASC
            """,
            fetch_all=True
        )
    
    # Get unique event types for filter buttons
    event_types = execute_query(
        "SELECT DISTINCT type FROM events WHERE type IS NOT NULL ORDER BY type",
        fetch_all=True
    )
    
    # Get registration count for each event
    events_with_counts = []
    for event in events or []:
        count = execute_query(
            "SELECT COUNT(*) as count FROM event_registrations WHERE event_id = %s",
            (event['id'],),
            fetch_one=True
        )
        event_dict = dict(event)
        event_dict['registration_count'] = count['count'] if count else 0
        events_with_counts.append(event_dict)
    
    return render_template(
        'events/list.html', 
        events=events_with_counts,
        event_types=event_types or [],
        current_type=event_type
    )


@events_bp.route('/view/<int:id>')
def view_event(id):
    """
    Display details of a specific event.
    Also checks if the current user is already registered.
    """
    # Fetch event details
    event = execute_query(
        """
        SELECT id, title, type, description, event_date, location, 
               max_participants, created_at 
        FROM events 
        WHERE id = %s
        """,
        (id,),
        fetch_one=True
    )
    
    if not event:
        flash('Event not found.', 'danger')
        return redirect(url_for('events.list_events'))
    
    # Check if user is registered (if logged in)
    is_registered = False
    if 'user_id' in session:
        registration = execute_query(
            "SELECT 1 FROM event_registrations WHERE user_id = %s AND event_id = %s",
            (session['user_id'], id),
            fetch_one=True
        )
        is_registered = registration is not None
    
    # Get registration count
    reg_count = execute_query(
        "SELECT COUNT(*) as count FROM event_registrations WHERE event_id = %s",
        (id,),
        fetch_one=True
    )
    
    # Get list of registered users (for display)
    registrations = execute_query(
        """
        SELECT u.id, u.full_name, u.profile_pic, er.registered_at as created_at
        FROM event_registrations er
        INNER JOIN users u ON er.user_id = u.id
        WHERE er.event_id = %s
        ORDER BY er.registered_at DESC
        LIMIT 10
        """,
        (id,),
        fetch_all=True
    )
    
    # Check if event is full
    max_participants = event.get('max_participants')
    is_full = False
    if max_participants and reg_count:
        is_full = reg_count['count'] >= max_participants
    
    return render_template(
        'events/details.html', 
        event=event,
        is_registered=is_registered,
        registration_count=reg_count['count'] if reg_count else 0,
        registrations=registrations or [],
        is_full=is_full
    )


@events_bp.route('/register/<int:id>', methods=['POST'])
@login_required
def register(id):
    """
    Register the current user for an event.
    """
    user_id = session['user_id']
    
    # Check if event exists
    event = execute_query(
        "SELECT id, title, max_participants FROM events WHERE id = %s",
        (id,),
        fetch_one=True
    )
    
    if not event:
        flash('Event not found.', 'danger')
        return redirect(url_for('events.list_events'))
    
    # Check if user is already registered
    existing = execute_query(
        "SELECT 1 FROM event_registrations WHERE user_id = %s AND event_id = %s",
        (user_id, id),
        fetch_one=True
    )
    
    if existing:
        flash('You are already registered for this event.', 'info')
        return redirect(url_for('events.view_event', id=id))
    
    # Check if event is full
    if event.get('max_participants'):
        reg_count = execute_query(
            "SELECT COUNT(*) as count FROM event_registrations WHERE event_id = %s",
            (id,),
            fetch_one=True
        )
        if reg_count and reg_count['count'] >= event['max_participants']:
            flash('This event is already full.', 'warning')
            return redirect(url_for('events.view_event', id=id))
    
    # Insert registration
    result = execute_query(
        "INSERT INTO event_registrations (user_id, event_id, registered_at) VALUES (%s, %s, NOW())",
        (user_id, id),
        commit=True
    )
    
    if result is not None:
        flash(f'Successfully registered for "{event["title"]}"!', 'success')
        
        # Create notification
        try:
            from notifications.utils import create_notification
            create_notification(
                user_id=user_id,
                message=f'You have registered for "{event["title"]}".',
                notification_type='event'
            )
        except Exception:
            pass
    else:
        flash('Failed to register. Please try again.', 'danger')
    
    return redirect(url_for('events.view_event', id=id))


@events_bp.route('/unregister/<int:id>', methods=['POST'])
@login_required
def unregister(id):
    """
    Unregister the current user from an event.
    """
    user_id = session['user_id']
    
    # Check if user is registered
    existing = execute_query(
        "SELECT 1 FROM event_registrations WHERE user_id = %s AND event_id = %s",
        (user_id, id),
        fetch_one=True
    )
    
    if not existing:
        flash('You are not registered for this event.', 'warning')
        return redirect(url_for('events.view_event', id=id))
    
    # Delete registration
    execute_query(
        "DELETE FROM event_registrations WHERE user_id = %s AND event_id = %s",
        (user_id, id),
        commit=True
    )
    
    flash('You have unregistered from this event.', 'info')
    return redirect(url_for('events.view_event', id=id))


@events_bp.route('/my-registrations')
@login_required
def my_registrations():
    """
    View all events the current user is registered for.
    """
    user_id = session['user_id']
    
    registrations = execute_query(
        """
        SELECT e.id, e.title, e.type, e.event_date, e.location, er.registered_at
        FROM event_registrations er
        INNER JOIN events e ON er.event_id = e.id
        WHERE er.user_id = %s
        ORDER BY e.event_date ASC
        """,
        (user_id,),
        fetch_all=True
    )
    
    return render_template('events/my_registrations.html', registrations=registrations or [])
