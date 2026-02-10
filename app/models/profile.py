from database.connection import get_db_connection

class Profile:
    @staticmethod
    def get_by_user_id(user_id):
        conn = get_db_connection()
        if not conn: return None
        try:
            with conn.cursor() as cursor:
                sql = "SELECT * FROM profiles WHERE user_id = %s"
                cursor.execute(sql, (user_id,))
                return cursor.fetchone()
        finally:
            conn.close()

    @staticmethod
    def create_or_update(user_id, data):
        conn = get_db_connection()
        if not conn: return False
        try:
            with conn.cursor() as cursor:
                # Check if exists
                sql_check = "SELECT profile_id FROM profiles WHERE user_id = %s"
                cursor.execute(sql_check, (user_id,))
                existing = cursor.fetchone()
                
                if existing:
                    # Update
                    sql = """
                        UPDATE profiles SET 
                        headline=%s, bio=%s, location=%s, phone=%s, 
                        profile_picture=%s, resume_path=%s, 
                        profile_completion=%s
                        WHERE user_id=%s
                    """
                    params = (
                        data.get('headline'), data.get('bio'), data.get('location'), 
                        data.get('phone'), data.get('profile_picture'), data.get('resume_path'),
                        data.get('profile_completion', 0), user_id
                    )
                    cursor.execute(sql, params)
                else:
                    # Create
                    sql = """
                        INSERT INTO profiles 
                        (user_id, headline, bio, location, phone, profile_picture, resume_path, profile_completion)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    params = (
                        user_id, data.get('headline'), data.get('bio'), data.get('location'), 
                        data.get('phone'), data.get('profile_picture'), data.get('resume_path'),
                        data.get('profile_completion', 0)
                    )
                    cursor.execute(sql, params)
            conn.commit()
            return True
        except Exception as e:
            print(f"Profile save error: {e}")
            return False
        finally:
            conn.close()

class Education:
    @staticmethod
    def get_by_user_id(user_id):
        conn = get_db_connection()
        if not conn: return []
        try:
            with conn.cursor() as cursor:
                sql = "SELECT * FROM education WHERE user_id = %s ORDER BY start_date DESC"
                cursor.execute(sql, (user_id,))
                return cursor.fetchall()
        finally:
            conn.close()

    @staticmethod
    def add(user_id, data):
        conn = get_db_connection()
        if not conn: return False
        try:
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO education 
                    (user_id, institution, degree, field_of_study, start_date, end_date, description)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                params = (
                    user_id, data.get('institution'), data.get('degree'), 
                    data.get('field_of_study'), data.get('start_date'), 
                    data.get('end_date'), data.get('description')
                )
                cursor.execute(sql, params)
            conn.commit()
            return True
        finally:
            conn.close()
            
    @staticmethod
    def delete(education_id, user_id):
        conn = get_db_connection()
        if not conn: return False
        try:
            with conn.cursor() as cursor:
                sql = "DELETE FROM education WHERE education_id = %s AND user_id = %s"
                cursor.execute(sql, (education_id, user_id))
            conn.commit()
            return True
        finally:
            conn.close()

class Skills:
    @staticmethod
    def get_all_skills():
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM skills ORDER BY skill_name")
                return cursor.fetchall()
        finally:
            conn.close()
            
    @staticmethod
    def get_user_skills(user_id):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                    SELECT us.*, s.skill_name 
                    FROM user_skills us
                    JOIN skills s ON us.skill_id = s.skill_id
                    WHERE us.user_id = %s
                """
                cursor.execute(sql, (user_id,))
                return cursor.fetchall()
        finally:
            conn.close()
            
    @staticmethod
    def add_user_skill(user_id, skill_id, proficiency):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO user_skills (user_id, skill_id, proficiency_level)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE proficiency_level = %s
                """
                cursor.execute(sql, (user_id, skill_id, proficiency, proficiency))
            conn.commit()
            return True
        finally:
            conn.close()
            
    @staticmethod
    def remove_user_skill(user_id, skill_id):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                sql = "DELETE FROM user_skills WHERE user_id = %s AND skill_id = %s"
                cursor.execute(sql, (user_id, skill_id))
            conn.commit()
            return True
        finally:
            conn.close()
