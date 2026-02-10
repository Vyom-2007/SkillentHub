from database.connection import get_db_connection
import bcrypt

class User:
    @staticmethod
    def create(email, password, full_name):
        conn = get_db_connection()
        if not conn:
            return None
        
        try:
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            with conn.cursor() as cursor:
                sql = "INSERT INTO users (email, password_hash, full_name) VALUES (%s, %s, %s)"
                cursor.execute(sql, (email, hashed, full_name))
                user_id = cursor.lastrowid
            conn.commit()
            return user_id
        except Exception as e:
            print(f"Error creating user: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def get_by_email(email):
        conn = get_db_connection()
        if not conn:
            return None
            
        try:
            with conn.cursor() as cursor:
                sql = "SELECT * FROM users WHERE email = %s"
                cursor.execute(sql, (email,))
                return cursor.fetchone()
        finally:
            conn.close()

    @staticmethod
    def get_by_id(user_id):
        conn = get_db_connection()
        if not conn:
            return None
            
        try:
            with conn.cursor() as cursor:
                sql = "SELECT * FROM users WHERE user_id = %s"
                cursor.execute(sql, (user_id,))
                return cursor.fetchone()
        finally:
            conn.close()

    @staticmethod
    def verify_password(stored_hash, password):
        return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
