from app.database.connection import get_db

class Job:
    @staticmethod
    def create(data):
        db = get_db()
        cursor = db.cursor()
        try:
            # data dict must contain recruiter_id and all fields
            fields = ['recruiter_id', 'title', 'location', 'job_type', 'work_mode', 
                      'experience_required', 'skills_required', 'salary_range', 
                      'description', 'requirements', 'perks_benefits', 'deadline', 'number_of_openings']
            
            # Construct query
            cols = ', '.join(fields)
            placeholders = ', '.join(['%s'] * len(fields))
            values = [data.get(f) for f in fields]
            
            cursor.execute(f"INSERT INTO jobs ({cols}) VALUES ({placeholders})", tuple(values))
            db.commit()
            return cursor.lastrowid
        except Exception as e:
            db.rollback()
            raise e
        finally:
            cursor.close()

    @staticmethod
    def get_all(filters=None):
        db = get_db()
        cursor = db.cursor()
        query = "SELECT j.*, r.full_name as company_name, rp.profile_picture as company_logo FROM jobs j JOIN recruiters r ON j.recruiter_id = r.recruiter_id JOIN recruiter_profiles rp ON r.recruiter_id = rp.recruiter_id WHERE status = 'active'"
        params = []
        if filters:
             if 'search' in filters and filters['search']:
                 query += " AND (title LIKE %s OR description LIKE %s OR r.full_name LIKE %s)"
                 term = f"%{filters['search']}%"
                 params.extend([term, term, term])
                 
        query += " ORDER BY posted_at DESC"
        cursor.execute(query, tuple(params))
        return cursor.fetchall()

    @staticmethod
    def get_by_id(job_id):
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT j.*, r.full_name as company_name, rp.profile_picture as company_logo, r.email as company_email
            FROM jobs j 
            JOIN recruiters r ON j.recruiter_id = r.recruiter_id 
            JOIN recruiter_profiles rp ON r.recruiter_id = rp.recruiter_id
            WHERE job_id = %s
        """, (job_id,))
        return cursor.fetchone()

    @staticmethod
    def get_by_recruiter(recruiter_id):
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT j.*, 
            (SELECT COUNT(*) FROM applications a WHERE a.item_type = 'job' AND a.item_id = j.job_id) as application_count
            FROM jobs j WHERE recruiter_id = %s ORDER BY posted_at DESC
        """, (recruiter_id,))
        return cursor.fetchall()
