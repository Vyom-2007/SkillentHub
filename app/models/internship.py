from app.database.connection import get_db

class Internship:
    @staticmethod
    def create(data):
        db = get_db()
        cursor = db.cursor()
        try:
            fields = ['recruiter_id', 'title', 'location', 'work_mode', 'duration',
                      'stipend', 'certificate_provided', 'ppo_possibility',
                      'skills_required', 'description', 'requirements', 'perks_benefits', 
                      'deadline', 'number_of_openings']
            
            cols = ', '.join(fields)
            placeholders = ', '.join(['%s'] * len(fields))
            values = [data.get(f) for f in fields]
            
            cursor.execute(f"INSERT INTO internships ({cols}) VALUES ({placeholders})", tuple(values))
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
        query = "SELECT i.*, r.full_name as company_name, rp.profile_picture as company_logo FROM internships i JOIN recruiters r ON i.recruiter_id = r.recruiter_id JOIN recruiter_profiles rp ON r.recruiter_id = rp.recruiter_id WHERE status = 'active'"
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
    def get_by_id(internship_id):
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT i.*, r.full_name as company_name, rp.profile_picture as company_logo, r.email as company_email
            FROM internships i 
            JOIN recruiters r ON i.recruiter_id = r.recruiter_id 
            JOIN recruiter_profiles rp ON r.recruiter_id = rp.recruiter_id
            WHERE internship_id = %s
        """, (internship_id,))
        return cursor.fetchone()
