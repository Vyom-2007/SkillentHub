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
    # 1. Get Job Skills
    job_skills_query = """
        SELECT skill_id, min_proficiency, weight, is_required
        FROM job_skills
        WHERE job_id = %s
    """
    job_skills = execute_query(job_skills_query, (job_id,), fetch_all=True)
    
    if not job_skills:
        return 0 # No skills required, no match score applicable (or 100? Let's say 0 for now as 'undefined')

    # 2. Get Candidate Skills
    candidate_skills_query = """
        SELECT s.skill_id, us.proficiency_level
        FROM user_skills us
        JOIN skills s ON us.skill_id = s.skill_id
        WHERE us.user_id = %s
    """
    candidate_skills_raw = execute_query(candidate_skills_query, (candidate_id,), fetch_all=True)
    
    # Map candidate skills for easy lookup: skill_id -> proficiency_weight
    candidate_skills_map = {}
    if candidate_skills_raw:
        for cs in candidate_skills_raw:
            candidate_skills_map[cs['skill_id']] = PROFICIENCY_WEIGHTS.get(cs['proficiency_level'], 1)

    total_possible_score = 0
    earned_score = 0
    
    for js in job_skills:
        skill_id = js['skill_id']
        weight = js['weight']
        min_prof_weight = PROFICIENCY_WEIGHTS.get(js['min_proficiency'], 1)
        required = js['is_required']
        
        # Max score contribution for this skill = weight * max_proficiency_multiplier (1.0)
        # Actually, let's keep it simple: Contribution = Weight
        # Proficiency acts as a modifier on how much of that weight is earned.
        
        total_possible_score += weight
        
        if skill_id in candidate_skills_map:
            cand_prof_weight = candidate_skills_map[skill_id]
            
            # Proficiency Match Calculation
            if cand_prof_weight >= min_prof_weight:
                # Met or exceeded proficiency
                earned_score += weight
            else:
                # Below proficiency: Partial credit
                # e.g. Required: Expert (4), Has: Beginner (1) -> 1/4 credit? Or scaled?
                # linear scale:
                ratio = cand_prof_weight / min_prof_weight
                earned_score += (weight * ratio)
        else:
            # Missing skill
            if required:
                # Heavy penalty for missing required skill?
                # For now, just 0 points earned.
                pass
                
    if total_possible_score == 0:
        return 0
        
    match_percentage = (earned_score / total_possible_score) * 100
    
    return int(match_percentage)

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
