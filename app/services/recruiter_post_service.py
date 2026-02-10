"""
Recruiter Post Service.
Handles creating new opportunities (jobs, internships, competitions, hackathons).
"""
from app.database.connection import execute_insert
from datetime import datetime

def create_job(recruiter_id, data):
    """
    Create a new job posting.
    """
    query = """
        INSERT INTO jobs (
            recruiter_id, title, location, job_type, work_mode, 
            experience_required, skills_required, salary_range, 
            description, requirements, deadline, number_of_openings
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        recruiter_id,
        data.get('title'),
        data.get('location'),
        data.get('job_type'),
        data.get('work_mode'),
        data.get('experience_required'),
        data.get('skills_required'),
        data.get('salary_range'),
        data.get('description'),
        data.get('requirements'),
        data.get('deadline'),
        data.get('openings', 1)
    )
    return execute_insert(query, params)

def create_internship(recruiter_id, data):
    """
    Create a new internship posting.
    """
    query = """
        INSERT INTO internships (
            recruiter_id, title, location, duration, stipend, 
            work_mode, certificate_provided, skills_required, 
            description, requirements, deadline
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        recruiter_id,
        data.get('title'),
        data.get('location'),
        data.get('duration'),
        data.get('stipend'),
        data.get('work_mode'),
        1 if data.get('certificate_provided') else 0,
        data.get('skills_required'),
        data.get('description'),
        data.get('requirements'),
        data.get('deadline')
    )
    return execute_insert(query, params)

def create_competition(recruiter_id, data):
    """
    Create a new competition.
    """
    query = """
        INSERT INTO competitions (
            recruiter_id, title, description, rules, 
            start_date, end_date, prize, max_participants
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        recruiter_id,
        data.get('title'),
        data.get('description'),
        data.get('rules'),
        data.get('start_date'),
        data.get('end_date'),
        data.get('prize_details'), # Maps to 'prize' column
        data.get('max_participants')
    )
    return execute_insert(query, params)

def create_hackathon(recruiter_id, data):
    """
    Create a new hackathon.
    """
    query = """
        INSERT INTO hackathons (
            recruiter_id, title, description, theme, 
            start_date, end_date, venue, mode, 
            team_size, prizes
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        recruiter_id,
        data.get('title'),
        data.get('description'),
        data.get('theme'),
        data.get('start_date'),
        data.get('end_date'),
        data.get('venue'),
        data.get('mode'),
        data.get('team_size'),
        data.get('prize_details') # Maps to 'prizes' column
    )
    return execute_insert(query, params)
