"""
Profile service module.
Handles profile CRUD, file uploads, skills, education, and visit tracking.
"""
import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app
from app.database.connection import execute_query, execute_insert


# Allowed file extensions for profile pictures and resumes
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
ALLOWED_RESUME_EXTENSIONS = {'pdf', 'doc', 'docx'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def allowed_file(filename, allowed_set):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_set


def save_profile_picture(file, user_id):
    """
    Save uploaded profile picture.
    Returns: Tuple (success, filename or error_message)
    """
    if not file or file.filename == '':
        return False, "No file selected"
    
    if not allowed_file(file.filename, ALLOWED_EXTENSIONS):
        return False, "Only JPG and PNG files are allowed"
    
    # Check file size
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    
    if size > MAX_FILE_SIZE:
        return False, "File size exceeds 5MB limit"
    
    # Create unique filename
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"profile_{user_id}_{uuid.uuid4().hex[:8]}.{ext}"
    
    # Ensure upload directory exists
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'profiles')
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save file
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)
    
    return True, filename


def save_profile_resume(file, user_id):
    """
    Save uploaded resume.
    Returns: Tuple (success, filename or error_message)
    """
    if not file or file.filename == '':
        return False, "No file selected"
    
    if not allowed_file(file.filename, ALLOWED_RESUME_EXTENSIONS):
        return False, "Only PDF, DOC, and DOCX files are allowed"
    
    # Check file size
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    
    if size > MAX_FILE_SIZE:
        return False, "File size exceeds 5MB limit"
    
    # Create unique filename
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"resume_{user_id}_{uuid.uuid4().hex[:8]}.{ext}"
    
    # Ensure upload directory exists
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'profile_resumes')
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save file
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)
    
    return True, filename


def delete_profile_picture(filename):
    """Delete a profile picture file."""
    if not filename:
        return
    filepath = os.path.join(current_app.root_path, 'static', 'uploads', 'profiles', filename)
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
        except OSError:
            pass


def delete_profile_resume(filename):
    """Delete a resume file."""
    if not filename:
        return
    filepath = os.path.join(current_app.root_path, 'static', 'uploads', 'profile_resumes', filename)
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
        except OSError:
            pass


# ==================== Profile CRUD ====================

def get_profile(user_id):
    """Get profile by user ID."""
    query = """
        SELECT p.*, u.email
        FROM profiles p
        JOIN users u ON p.user_id = u.user_id
        WHERE p.user_id = %s
    """
    return execute_query(query, (user_id,), fetch_one=True)


def profile_exists(user_id):
    """Check if a profile exists for user."""
    query = "SELECT profile_id FROM profiles WHERE user_id = %s"
    result = execute_query(query, (user_id,), fetch_one=True)
    return result is not None


def create_profile(user_id, data, profile_picture=None, resume_file=None):
    """Create a new profile."""
    picture_filename = None
    resume_filename = None
    
    if profile_picture and profile_picture.filename:
        success, result = save_profile_picture(profile_picture, user_id)
        if not success:
            return False, result
        picture_filename = result
        
    if resume_file and resume_file.filename:
        success, result = save_profile_resume(resume_file, user_id)
        if not success:
            # Cleanup picture if resume failed
            if picture_filename: delete_profile_picture(picture_filename)
            return False, result
        resume_filename = result
    
    try:
        query = """
            INSERT INTO profiles (
                user_id, full_name, headline, bio, location, phone, profile_picture,
                resume_path, show_skills, show_education, show_experience, show_resume
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        execute_insert(query, (
            user_id,
            data.get('full_name'),
            data.get('headline'),
            data.get('bio'),
            data.get('location'),
            data.get('phone'),
            picture_filename,
            resume_filename,
            data.get('show_skills', 1),
            data.get('show_education', 1),
            data.get('show_experience', 1),
            data.get('show_resume', 0)
        ))
        return True, "Profile created successfully"
    except Exception as e:
        return False, str(e)


def update_profile(user_id, data, profile_picture=None, resume_file=None):
    """Update an existing profile."""
    existing = get_profile(user_id)
    picture_filename = existing.get('profile_picture') if existing else None
    resume_filename = existing.get('resume_path') if existing else None
    
    if profile_picture and profile_picture.filename:
        if picture_filename:
            delete_profile_picture(picture_filename)
        success, result = save_profile_picture(profile_picture, user_id)
        if not success:
            return False, result
        picture_filename = result
        
    if resume_file and resume_file.filename:
        if resume_filename:
            delete_profile_resume(resume_filename)
        success, result = save_profile_resume(resume_file, user_id)
        if not success:
            return False, result
        resume_filename = result
    
    try:
        # Defensive values for NOT NULL columns
        full_name = data.get('full_name')
        if full_name is None:
            full_name = existing.get('full_name') if existing else ''
            
        show_skills = int(data.get('show_skills', 1))
        show_education = int(data.get('show_education', 1)) 
        show_experience = int(data.get('show_experience', 1))
        show_resume = int(data.get('show_resume', 0))

        query = """
            UPDATE profiles 
            SET full_name = %s, headline = %s, bio = %s, 
                location = %s, phone = %s, profile_picture = %s,
                resume_path = %s, show_skills = %s, show_education = %s,
                show_experience = %s, show_resume = %s,
                updated_at = NOW()
            WHERE user_id = %s
        """
        params = (
            full_name,
            data.get('headline'),
            data.get('bio'),
            data.get('location'),
            data.get('phone'),
            picture_filename,
            resume_filename,
            show_skills,
            show_education,
            show_experience,
            show_resume,
            user_id
        )
        execute_query(query, params)
        return True, "Profile updated successfully"
    except Exception as e:
        current_app.logger.error(f"Error updating profile user_id={user_id}: {e}")
        # Log params for debugging
        current_app.logger.error(f"Params: {locals().get('params')}")
        return False, f"Database error: {str(e)}"


def get_profile_with_details(user_id):
    """Get complete profile with skills and education."""
    profile = get_profile(user_id)
    if not profile:
        return None
    
    profile['skills'] = get_user_skills(user_id)
    profile['education'] = get_user_education(user_id)
    profile['experience'] = get_user_experience(user_id)
    profile['completion'] = calculate_profile_completion(profile)
    
    return profile


def get_user_experience(user_id):
    """Get experience entries for a user."""
    query = """
        SELECT * FROM experience 
        WHERE user_id = %s 
        ORDER BY start_date DESC
    """
    return execute_query(query, (user_id,), fetch_all=True)


# ==================== Skills Management ====================

def get_all_skills():
    """Get all available skills."""
    query = "SELECT skill_id, skill_name FROM skills ORDER BY skill_name"
    return execute_query(query, fetch_all=True) or []


def get_user_skills(user_id):
    """Get skills for a user."""
    query = """
        SELECT s.skill_id, s.skill_name, us.proficiency_level
        FROM user_skills us
        JOIN skills s ON us.skill_id = s.skill_id
        WHERE us.user_id = %s
        ORDER BY s.skill_name
    """
    return execute_query(query, (user_id,), fetch_all=True) or []


def update_user_skills(user_id, skill_ids):
    """Update user's skills (replace all)."""
    from app.database.connection import get_db_connection
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Delete existing skills
            cursor.execute("DELETE FROM user_skills WHERE user_id = %s", (user_id,))
            
            # Insert new skills
            if skill_ids:
                for skill_id in skill_ids:
                    try:
                        cursor.execute(
                            "INSERT INTO user_skills (user_id, skill_id) VALUES (%s, %s)",
                            (user_id, int(skill_id))
                        )
                    except Exception as e:
                        print(f"Error inserting skill {skill_id}: {e}")
                        pass  # Ignore duplicates or errors
    except Exception as e:
        print(f"Error updating skills: {e}")


def add_skill_if_not_exists(skill_name):
    """Add a new skill if it doesn't exist, return skill_id."""
    query = "SELECT skill_id FROM skills WHERE skill_name = %s"
    existing = execute_query(query, (skill_name.strip(),), fetch_one=True)
    
    if existing:
        return existing['skill_id']
    
    return execute_insert("INSERT INTO skills (skill_name) VALUES (%s)", (skill_name.strip(),))


# ==================== Education Management ====================

def get_user_education(user_id):
    """Get education entries for a user."""
    query = """
        SELECT education_id, institution_name, degree, field_of_study,
               start_year, end_year, description
        FROM education
        WHERE user_id = %s
        ORDER BY start_year DESC
    """
    return execute_query(query, (user_id,), fetch_all=True) or []


def add_education(user_id, data):
    """Add a new education entry."""
    query = """
        INSERT INTO education 
        (user_id, institution_name, degree, field_of_study, start_year, end_year, description)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    return execute_insert(query, (
        user_id,
        data.get('institution_name'),
        data.get('degree'),
        data.get('field_of_study'),
        data.get('start_year') or None,
        data.get('end_year') or None,
        data.get('description')
    ))


def delete_education(education_id, user_id):
    """Delete an education entry (verify ownership)."""
    query = "DELETE FROM education WHERE education_id = %s AND user_id = %s"
    return execute_query(query, (education_id, user_id))


def save_education_entries(user_id, education_list):
    """Save multiple education entries for setup/edit."""
    # Delete existing
    execute_query("DELETE FROM education WHERE user_id = %s", (user_id,))
    
    # Insert new
    for edu in education_list:
        if edu.get('institution_name') and edu.get('degree'):
            add_education(user_id, edu)


# ==================== Profile Visits ====================

def record_visit(profile_user_id, visitor_user_id=None, visitor_recruiter_id=None):
    """Record a profile visit (if not visited today)."""
    # Don't record self-visits
    if visitor_user_id == profile_user_id:
        return
    
    # Check if already visited today
    if visitor_user_id:
        check_query = """
            SELECT visit_id FROM profile_visits
            WHERE profile_user_id = %s AND visitor_user_id = %s AND DATE(visited_at) = CURDATE()
        """
        if execute_query(check_query, (profile_user_id, visitor_user_id), fetch_one=True):
            return

    if visitor_recruiter_id:
        check_query = """
            SELECT visit_id FROM profile_visits
            WHERE profile_user_id = %s AND visitor_recruiter_id = %s AND DATE(visited_at) = CURDATE()
        """
        if execute_query(check_query, (profile_user_id, visitor_recruiter_id), fetch_one=True):
            return
    
    # Record visit
    insert_query = """
        INSERT INTO profile_visits (profile_user_id, visitor_user_id, visitor_recruiter_id)
        VALUES (%s, %s, %s)
    """
    execute_insert(insert_query, (profile_user_id, visitor_user_id, visitor_recruiter_id))


def get_visit_stats(user_id):
    """Get profile visit statistics."""
    query = """
        SELECT 
            COUNT(CASE WHEN visitor_user_id IS NOT NULL THEN 1 END) as user_visits,
            COUNT(CASE WHEN visitor_recruiter_id IS NOT NULL THEN 1 END) as recruiter_visits,
            COUNT(*) as total_visits
        FROM profile_visits
        WHERE profile_user_id = %s
    """
    result = execute_query(query, (user_id,), fetch_one=True)
    
    if not result:
        return {
            'user_visits': 0,
            'recruiter_visits': 0,
            'total_visits': 0
        }
    
    return {
        'user_visits': result.get('user_visits') or 0,
        'recruiter_visits': result.get('recruiter_visits') or 0,
        'total_visits': result.get('total_visits') or 0
    }


# ==================== Profile Completion ====================

def calculate_profile_completion(profile):
    """Calculate profile completion percentage."""
    if not profile:
        return 0
    
    total_fields = 8
    completed = 0
    
    if profile.get('full_name'): completed += 1
    if profile.get('headline'): completed += 1
    if profile.get('bio'): completed += 1
    if profile.get('location'): completed += 1
    if profile.get('phone'): completed += 1
    if profile.get('profile_picture'): completed += 1
    if profile.get('skills') and len(profile['skills']) > 0: completed += 1
    if profile.get('education') and len(profile['education']) > 0: completed += 1
    
    return int((completed / total_fields) * 100)


# ==================== User Posts ====================

def get_user_posts(user_id, limit=10):
    """Get posts by a user for their profile."""
    query = """
        SELECT p.post_id, p.content, p.image_path, p.created_at,
               (SELECT COUNT(*) FROM post_likes WHERE post_id = p.post_id) as likes_count
        FROM posts p
        WHERE p.author_id = %s
        ORDER BY p.created_at DESC
        LIMIT %s
    """
    return execute_query(query, (user_id, limit), fetch_all=True) or []

# ==================== Achievements / Wins ====================

def get_user_wins(user_id):
    """
    Get hackathon and competition wins for a user.
    Returns list of wins with event details and team members.
    """
    # Query to get teams the user is part of that have a rank
    # NOTE: 'rank' column is missing in teams table schema. Returning empty list to prevent crash.
    # query = """
    #     SELECT 
    #         t.team_id, t.team_name, t.rank,
    #         c.title as competition_title, c.competition_id,
    #         h.title as hackathon_title, h.hackathon_id,
    #         CASE 
    #             WHEN c.competition_id IS NOT NULL THEN 'Competition'
    #             WHEN h.hackathon_id IS NOT NULL THEN 'Hackathon'
    #         END as event_type,
    #         CASE 
    #             WHEN c.competition_id IS NOT NULL THEN c.title
    #             WHEN h.hackathon_id IS NOT NULL THEN h.title
    #         END as event_title,
    #         CASE 
    #             WHEN c.competition_id IS NOT NULL THEN c.end_date
    #             WHEN h.hackathon_id IS NOT NULL THEN h.end_date
    #         END as event_date
    #     FROM teams t
    #     JOIN team_members tm ON t.team_id = tm.team_id
    #     LEFT JOIN competitions c ON t.item_type = 'competition' AND t.item_id = c.competition_id
    #     LEFT JOIN hackathons h ON t.item_type = 'hackathon' AND t.item_id = h.hackathon_id
    #     WHERE tm.user_id = %s 
    #     AND t.rank IS NOT NULL 
    #     AND t.rank != ''
    #     ORDER BY event_date DESC
    # """
    # wins = execute_query(query, (user_id,), fetch_all=True)
    
    # if not wins:
    #     return []
        
    # # For each win, get team members
    # for win in wins:
    #     members_query = """
    #         SELECT u.user_id, p.full_name, p.profile_picture
    #         FROM team_members tm
    #         JOIN users u ON tm.user_id = u.user_id
    #         LEFT JOIN profiles p ON u.user_id = p.user_id
    #         WHERE tm.team_id = %s
    #     """
    #     win['members'] = execute_query(members_query, (win['team_id'],), fetch_all=True)
        
    # return wins
    return []
