from app.database.connection import get_db
import random
import string
from datetime import datetime, timedelta

class PasswordResetOTP:
    @staticmethod
    def create(email, user_id=None, recruiter_id=None):
        db = get_db()
        cursor = db.cursor()
        
        otp = ''.join(random.choices(string.digits, k=6))
        expires_at = datetime.now() + timedelta(minutes=5)
        
        try:
            cursor.execute(
                """INSERT INTO password_reset_otps 
                   (user_id, recruiter_id, email, otp, expires_at) 
                   VALUES (%s, %s, %s, %s, %s)""",
                (user_id, recruiter_id, email, otp, expires_at)
            )
            db.commit()
            return otp
        except Exception as e:
            db.rollback()
            raise e
        finally:
            cursor.close()

    @staticmethod
    def verify(email, otp):
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute(
            """SELECT * FROM password_reset_otps 
               WHERE email = %s AND otp = %s AND is_used = 0 
               ORDER BY created_at DESC LIMIT 1""",
            (email, otp)
        )
        record = cursor.fetchone()
        
        valid = False
        if record:
            if record['expires_at'] > datetime.now():
                valid = True
            else:
                # Mark as used/expired? Maybe not needed as we check expires_at
                pass
        
        cursor.close()
        return valid, record
        
    @staticmethod
    def mark_used(otp_id):
        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute("UPDATE password_reset_otps SET is_used = 1 WHERE otp_id = %s", (otp_id,))
            db.commit()
        except:
            db.rollback()
        finally:
            cursor.close()
