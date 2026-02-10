from app.database.connection import get_db
import bcrypt

class Recruiter:
    @staticmethod
    def create(email, password, full_name):
        db = get_db()
        cursor = db.cursor()
        
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        try:
            cursor.execute(
                "INSERT INTO recruiters (email, password_hash, full_name) VALUES (%s, %s, %s)",
                (email, password_hash, full_name)
            )
            recruiter_id = cursor.lastrowid
            
            # Create empty profile
            cursor.execute(
                "INSERT INTO recruiter_profiles (recruiter_id) VALUES (%s)",
                (recruiter_id,)
            )
            
            db.commit()
            return recruiter_id
        except Exception as e:
            db.rollback()
            raise e
        finally:
            cursor.close()

    @staticmethod
    def get_by_email(email):
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM recruiters WHERE email = %s", (email,))
        recruiter = cursor.fetchone()
        cursor.close()
        return recruiter

    @staticmethod
    def get_by_id(recruiter_id):
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM recruiters WHERE recruiter_id = %s", (recruiter_id,))
        recruiter = cursor.fetchone()
        cursor.close()
        return recruiter

    @staticmethod
    def verify_password(stored_hash, password):
        return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
