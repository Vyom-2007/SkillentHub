from app.database.connection import get_db

class RecruiterProfile:
    @staticmethod
    def get_by_recruiter_id(recruiter_id):
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT p.*, r.full_name, r.email 
            FROM recruiter_profiles p 
            JOIN recruiters r ON p.recruiter_id = r.recruiter_id 
            WHERE p.recruiter_id = %s
        """, (recruiter_id,))
        return cursor.fetchone()

    @staticmethod
    def update(recruiter_id, data):
        db = get_db()
        cursor = db.cursor()
        
        allowed_fields = ['headline', 'bio', 'location', 'phone', 'profile_picture']
        updates = []
        values = []
        
        for field in allowed_fields:
            if field in data:
                updates.append(f"{field} = %s")
                values.append(data[field])
                
        if not updates:
            return False
            
        values.append(recruiter_id)
        query = f"UPDATE recruiter_profiles SET {', '.join(updates)} WHERE recruiter_id = %s"
        
        try:
            cursor.execute(query, tuple(values))
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise e
        finally:
            cursor.close()
