from app.database.connection import get_db

class Competition:
    @staticmethod
    def create(data):
        db = get_db()
        cursor = db.cursor()
        try:
            fields = ['recruiter_id', 'title', 'description', 'requirements', 'prizes', 
                      'deadline', 'start_date', 'end_date', 'location', 'type'] # type: hackathon, coding, design, etc.
            
            cols = ', '.join(fields)
            placeholders = ', '.join(['%s'] * len(fields))
            values = [data.get(f) for f in fields]
            
            cursor.execute(f"INSERT INTO competitions ({cols}) VALUES ({placeholders})", tuple(values))
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
        query = "SELECT c.*, r.full_name as organizer, rp.profile_picture as organizer_logo FROM competitions c JOIN recruiters r ON c.recruiter_id = r.recruiter_id JOIN recruiter_profiles rp ON r.recruiter_id = rp.recruiter_id WHERE status = 'active'"
        params = []
        if filters:
             if 'search' in filters and filters['search']:
                 query += " AND (title LIKE %s OR description LIKE %s)"
                 term = f"%{filters['search']}%"
                 params.extend([term, term])
                 
        query += " ORDER BY posted_at DESC"
        cursor.execute(query, tuple(params))
        return cursor.fetchall()

    @staticmethod
    def get_by_id(competition_id):
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT c.*, r.full_name as company_name, rp.profile_picture as company_logo
            FROM competitions c
            JOIN recruiters r ON c.recruiter_id = r.recruiter_id 
            JOIN recruiter_profiles rp ON r.recruiter_id = rp.recruiter_id
            WHERE competition_id = %s
        """, (competition_id,))
        return cursor.fetchone()
