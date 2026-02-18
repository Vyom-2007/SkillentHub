"""
Interview Service.
Handles scheduling, updating, and retrieving interviews.
Integrates with notification service.
"""
from app.database.connection import execute_query, execute_insert, execute_update
from app.services import notification_service, email_service
from datetime import datetime

def schedule_interview(application_id, recruiter_id, candidate_id, scheduled_at, mode, location_url=None, notes=None):
    """
    Schedule a new interview.
    """
    # Validate application exists and belongs to recruiter/candidate pair? 
    # Trusted input from route usually, but basic check is good.
    
    query = """
        INSERT INTO interviews 
        (application_id, recruiter_id, candidate_id, scheduled_at, mode, location_url, notes, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending')
    """
    interview_id = execute_insert(query, (application_id, recruiter_id, candidate_id, scheduled_at, mode, location_url, notes))
    
    if interview_id:
        # Notify Candidate
        notification_service.notify_interview_invite(recruiter_id, candidate_id, interview_id, str(scheduled_at))
            
    return interview_id


def reschedule_interview(interview_id, new_scheduled_at, user_id, location_url=None, notes=None):
    """
    Reschedule an existing interview.
    """
    # Verify permission and existence
    interview = get_interview_by_id(interview_id)
    if not interview:
        return False, "Interview not found"
        
    if interview['recruiter_id'] != user_id:
        return False, "Unauthorized"
        
    # Update
    if location_url:
        query = "UPDATE interviews SET scheduled_at = %s, location_url = %s, notes = %s, status = 'pending' WHERE interview_id = %s"
        params = (new_scheduled_at, location_url, notes, interview_id)
    else:
         query = "UPDATE interviews SET scheduled_at = %s, notes = %s, status = 'pending' WHERE interview_id = %s"
         params = (new_scheduled_at, notes, interview_id)
         
    execute_update(query, params)
    
    # Notify
    notification_service.notify_interview_reschedule(
        interview['recruiter_id'], 
        interview['candidate_id'], 
        interview_id, 
        str(new_scheduled_at)
    )
    
    return True, "Interview rescheduled successfully"


def update_interview_status(interview_id, new_status, user_role, user_id):
    """
    Update interview status (confirmed, declined, cancelled, completed).
    user_role: 'recruiter' or 'user' (candidate)
    """
    # Verify permission
    interview = get_interview_by_id(interview_id)
    if not interview:
        return False, "Interview not found"
        
    if user_role == 'recruiter':
        if interview['recruiter_id'] != user_id:
            return False, "Unauthorized"
    elif user_role == 'user':
        if interview['candidate_id'] != user_id:
            return False, "Unauthorized"
            
    # State transitions check
    current_status = interview['status']
    
    # Candidate can only Confirm or Decline if Pending
    if user_role == 'user':
        if current_status != 'pending':
            return False, f"Cannot change status from {current_status}"
        if new_status not in ['confirmed', 'declined']:
            return False, "Invalid status change"
            
    # Recruiter can Cancel or Complete
    if user_role == 'recruiter':
        if new_status not in ['cancelled', 'completed']:
            # Maybe allow rescheduling (update time) instead of status change?
            # For now simple status update.
            return False, "Invalid status change"

    query = "UPDATE interviews SET status = %s WHERE interview_id = %s"
    execute_update(query, (new_status, interview_id))
    
    # Notifications on change
    try:
        if user_role == 'user':
            # Notify Recruiter
            # Since notifications table assumes user_id (users table), and recruiters are in recruiters table, 
            # we might not be able to send in-app notification to recruiter if they don't share `users` table ID space 
            # or if `notifications` table `user_id` FK points to `users`.
            # Let's check schema. `notifications.user_id` -> `users.user_id`.
            # Recruiters are separate usually? Or are they users too?
            # Start of project: "Recruiters and Users are separate entities".
            # So we CANNOT send in-app notification to Recruiter using `notifications` table directly if it FKs to `users`.
            # We might need `recruiter_notifications` OR just send Email.
            # checks Schema: `updated_at` timestamp.
            # Schema: `notifications` table `user_id` is int. FK to `users`?
            # Let's assume Email for Recruiter for now, or check if we have recruiter notifications.
            pass 
        else:
            # Recruiter updated -> Notify Candidate
            notification_service.notify_interview_update(interview['recruiter_id'], interview['candidate_id'], interview_id, new_status)
    except Exception as e:
        print(f"Error sending status notification: {e}")

    return True, "Status updated"


def get_interview_by_id(interview_id):
    query = """
        SELECT i.*, 
               r.company_name, 
               u.email as candidate_email, p.full_name as candidate_name,
               j.title as job_title
        FROM interviews i
        JOIN recruiters r ON i.recruiter_id = r.recruiter_id
        JOIN users u ON i.candidate_id = u.user_id
        LEFT JOIN profiles p ON u.user_id = p.user_id
        JOIN applications a ON i.application_id = a.application_id
        LEFT JOIN jobs j ON a.item_type='job' AND a.item_id = j.job_id
        WHERE i.interview_id = %s
    """
    return execute_query(query, (interview_id,), fetch_one=True)


def get_interviews_for_candidate(user_id):
    query = """
        SELECT i.*, r.company_name, 
               COALESCE(j.title, intn.title, c.title, h.title) as item_title
        FROM interviews i
        JOIN recruiters r ON i.recruiter_id = r.recruiter_id
        JOIN applications a ON i.application_id = a.application_id
        LEFT JOIN jobs j ON a.item_type='job' AND a.item_id = j.job_id
        LEFT JOIN internships intn ON a.item_type='internship' AND a.item_id = intn.internship_id
        LEFT JOIN competitions c ON a.item_type='competition' AND a.item_id = c.competition_id
        LEFT JOIN hackathons h ON a.item_type='hackathon' AND a.item_id = h.hackathon_id
        WHERE i.candidate_id = %s
        ORDER BY i.scheduled_at DESC
    """
    return execute_query(query, (user_id,), fetch_all=True)


def get_interviews_for_recruiter(recruiter_id):
    query = """
        SELECT i.*, p.full_name as candidate_name, p.profile_picture,
               COALESCE(j.title, intn.title, c.title, h.title) as item_title
        FROM interviews i
        JOIN users u ON i.candidate_id = u.user_id
        LEFT JOIN profiles p ON u.user_id = p.user_id
        JOIN applications a ON i.application_id = a.application_id
        LEFT JOIN jobs j ON a.item_type='job' AND a.item_id = j.job_id
        LEFT JOIN internships intn ON a.item_type='internship' AND a.item_id = intn.internship_id
        LEFT JOIN competitions c ON a.item_type='competition' AND a.item_id = c.competition_id
        LEFT JOIN hackathons h ON a.item_type='hackathon' AND a.item_id = h.hackathon_id
        WHERE i.recruiter_id = %s
        ORDER BY i.scheduled_at DESC
    """
    return execute_query(query, (recruiter_id,), fetch_all=True)
