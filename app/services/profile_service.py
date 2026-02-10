from app.database.connection import get_db_connection


# ── Read Operations ───────────────────────────────────────────

def get_profile(user_id):
    """Get user + profile data (LEFT JOIN so it works even without a profile row)."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT u.user_id, u.email, u.full_name, u.created_at, "
                "       p.profile_id, p.headline, p.bio, p.profile_picture, "
                "       p.location, p.phone, p.resume_path, p.cover_letter_path, "
                "       p.profile_visits_by_users, p.profile_visits_by_recruiters, "
                "       p.profile_completion "
                "FROM users u "
                "LEFT JOIN profiles p ON u.user_id = p.user_id "
                "WHERE u.user_id = %s",
                (user_id,),
            )
            return cur.fetchone()
    finally:
        conn.close()


def get_education(user_id):
    """Get all education entries for a user, newest first."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM education WHERE user_id = %s ORDER BY start_date DESC",
                (user_id,),
            )
            return cur.fetchall()
    finally:
        conn.close()


def get_user_skills(user_id):
    """Get skills with proficiency for a user."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT s.skill_id, s.skill_name, us.proficiency_level "
                "FROM user_skills us "
                "JOIN skills s ON us.skill_id = s.skill_id "
                "WHERE us.user_id = %s "
                "ORDER BY s.skill_name",
                (user_id,),
            )
            return cur.fetchall()
    finally:
        conn.close()


def get_user_posts(user_id):
    """Get all posts by the user, newest first."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM posts "
                "WHERE author_id = %s AND author_type = 'user' "
                "ORDER BY created_at DESC",
                (user_id,),
            )
            return cur.fetchall()
    finally:
        conn.close()


def get_full_profile(user_id):
    """
    Assemble a complete profile dict:
    { profile, education, skills, posts, completion }
    """
    profile = get_profile(user_id)
    if not profile:
        return None

    education = get_education(user_id)
    skills = get_user_skills(user_id)
    posts = get_user_posts(user_id)
    completion = calculate_completion(profile, education, skills)

    return {
        'profile': profile,
        'education': education,
        'skills': skills,
        'posts': posts,
        'completion': completion,
    }


# ── Write Operations ──────────────────────────────────────────

def upsert_profile(user_id, data):
    """
    Insert or update the profiles row.
    data keys: headline, bio, location, phone, profile_picture,
               resume_path, cover_letter_path.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Check if profile exists
            cur.execute("SELECT profile_id FROM profiles WHERE user_id = %s", (user_id,))
            exists = cur.fetchone()

            if exists:
                set_clauses = []
                values = []
                for key in ('headline', 'bio', 'location', 'phone',
                            'profile_picture', 'resume_path', 'cover_letter_path'):
                    if key in data and data[key] is not None:
                        set_clauses.append(f"{key} = %s")
                        values.append(data[key])

                if set_clauses:
                    values.append(user_id)
                    cur.execute(
                        f"UPDATE profiles SET {', '.join(set_clauses)} WHERE user_id = %s",
                        values,
                    )
            else:
                cur.execute(
                    "INSERT INTO profiles (user_id, headline, bio, location, phone, "
                    "profile_picture, resume_path, cover_letter_path) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (
                        user_id,
                        data.get('headline', ''),
                        data.get('bio', ''),
                        data.get('location', ''),
                        data.get('phone', ''),
                        data.get('profile_picture'),
                        data.get('resume_path'),
                        data.get('cover_letter_path'),
                    ),
                )
    finally:
        conn.close()


def save_skills(user_id, skills_list):
    """
    Replace all skills for a user.
    skills_list: [{ 'name': str, 'proficiency': str }, ...]
    """
    if not skills_list:
        return

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Remove existing user_skills
            cur.execute("DELETE FROM user_skills WHERE user_id = %s", (user_id,))

            for skill in skills_list:
                name = skill.get('name', '').strip()
                proficiency = skill.get('proficiency', 'beginner')
                if not name:
                    continue

                # Ensure proficiency is valid
                if proficiency not in ('beginner', 'intermediate', 'advanced'):
                    proficiency = 'beginner'

                # Upsert into skills table
                cur.execute(
                    "INSERT INTO skills (skill_name) VALUES (%s) "
                    "ON DUPLICATE KEY UPDATE skill_id = LAST_INSERT_ID(skill_id)",
                    (name,),
                )
                skill_id = cur.lastrowid
                if not skill_id:
                    cur.execute("SELECT skill_id FROM skills WHERE skill_name = %s", (name,))
                    row = cur.fetchone()
                    skill_id = row['skill_id'] if row else None

                if skill_id:
                    cur.execute(
                        "INSERT INTO user_skills (user_id, skill_id, proficiency_level) "
                        "VALUES (%s, %s, %s)",
                        (user_id, skill_id, proficiency),
                    )
    finally:
        conn.close()


def save_education(user_id, edu_list):
    """
    Replace all education entries for a user.
    edu_list: [{ institution, degree, field_of_study, start_date, end_date, description }, ...]
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Remove old entries
            cur.execute("DELETE FROM education WHERE user_id = %s", (user_id,))

            for edu in edu_list:
                institution = edu.get('institution', '').strip()
                degree = edu.get('degree', '').strip()
                if not institution or not degree:
                    continue

                cur.execute(
                    "INSERT INTO education "
                    "(user_id, institution, degree, field_of_study, start_date, end_date, description) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (
                        user_id,
                        institution,
                        degree,
                        edu.get('field_of_study', ''),
                        edu.get('start_date') or None,
                        edu.get('end_date') or None,
                        edu.get('description', ''),
                    ),
                )
    finally:
        conn.close()


def update_profile_completion(user_id):
    """Recalculate and store profile completion percentage."""
    profile = get_profile(user_id)
    education = get_education(user_id)
    skills = get_user_skills(user_id)
    completion = calculate_completion(profile, education, skills)

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE profiles SET profile_completion = %s WHERE user_id = %s",
                (completion, user_id),
            )
    finally:
        conn.close()

    return completion


def increment_visit(user_id, visitor_type='user'):
    """Increment the profile visit counter."""
    col = 'profile_visits_by_recruiters' if visitor_type == 'recruiter' else 'profile_visits_by_users'
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE profiles SET {col} = {col} + 1 WHERE user_id = %s",
                (user_id,),
            )
    finally:
        conn.close()


# ── Helpers ───────────────────────────────────────────────────

def calculate_completion(profile, education, skills):
    """
    Weighted profile completion score.
    headline 15%, bio 15%, picture 15%, location 10%,
    phone 10%, resume 10%, education 15%, skills 10%
    """
    if not profile:
        return 0

    score = 0
    if profile.get('headline'):
        score += 15
    if profile.get('bio'):
        score += 15
    if profile.get('profile_picture'):
        score += 15
    if profile.get('location'):
        score += 10
    if profile.get('phone'):
        score += 10
    if profile.get('resume_path'):
        score += 10
    if education and len(education) > 0:
        score += 15
    if skills and len(skills) > 0:
        score += 10

    return score
