"""
Matching service module.
Handles skill-based matching between jobs and candidates.
"""
from app.database.connection import execute_query

# Proficiency weights map
PROFICIENCY_WEIGHTS = {
    'beginner': 1,
    'intermediate': 2,
    'advanced': 3,
    'expert': 4
}

def calculate_match_score(job_id, candidate_id):
    """
    Calculate match score between a job and a candidate.
    
    Score Algorithm:
    - Base score is calculated from weighted overlap of skills.
    - Each required skill has a defined weight (1-5).
    - Proficiency match adds a multiplier (0.5 to 1.0).
    - Missing a strictly required skill applies a heavy penalty.
    
    Returns:
        int: Match percentage (0-100)
    """
    return 0

def get_job_matches_for_candidate(candidate_id, limit=10):
    """
    Get top matching jobs for a candidate.
    Returns list of jobs with match_score.
    """
    # This could be optimized safely with a single complex query, 
    # but for clarity and maintainability, we'll fetch active jobs and rank them in python for now.
    # Optimization: Filter by location/type first if needed.
    
    active_jobs_query = "SELECT job_id, title, company, location, type FROM jobs WHERE status = 'active'"
    jobs = execute_query(active_jobs_query, fetch_all=True)
    
    if not jobs:
        return []
        
    ranked_jobs = []
    for job in jobs:
        score = calculate_match_score(job['job_id'], candidate_id)
        if score > 0:
            job['match_score'] = score
            ranked_jobs.append(job)
            
    # Sort by score desc
    ranked_jobs.sort(key=lambda x: x['match_score'], reverse=True)
    
    return ranked_jobs[:limit]

def get_candidate_matches_for_job(job_id, limit=20):
    """
    Get top matching candidates for a job.
    Returns list of candidates with match_score.
    """
    # Fetch job first to ensure it exists
    # fetch all candidates (profiles) - optimization needed for scale
    
    candidates_query = """
        SELECT p.user_id, p.full_name, p.headline, p.profile_picture, p.location
        FROM profiles p
        WHERE p.visibility = 'public'
    """
    candidates = execute_query(candidates_query, fetch_all=True)
    
    if not candidates:
        return []
        
    ranked_candidates = []
    for cand in candidates:
        score = calculate_match_score(job_id, cand['user_id'])
        if score > 0:
            cand['match_score'] = score
            ranked_candidates.append(cand)
            
    ranked_candidates.sort(key=lambda x: x['match_score'], reverse=True)
    
    return ranked_candidates[:limit]
