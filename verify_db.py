import pymysql
from config import Config

def verify():
    try:
        conn = pymysql.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB
        )
        cursor = conn.cursor()
        
        cursor.execute("SHOW TABLES")
        tables = [t[0] for t in cursor.fetchall()]
        print("Existing Tables:", tables)
        
        expected = [
            'users', 'recruiters', 'profiles', 'recruiter_profiles', 
            'skills', 'user_skills', 'education', 'jobs', 'internships', 
            'competitions', 'applications', 'posts', 'post_likes', 
            'comments', 'connections', 'messages', 'notifications', 
            'password_reset_otps'
        ]
        
        missing = [t for t in expected if t not in tables]
        
        if missing:
            print(f"MISSING TABLES: {missing}")
        else:
            print("All expected tables present.")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify()
