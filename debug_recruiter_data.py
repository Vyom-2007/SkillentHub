from app import create_app
from app.database.connection import get_db_connection

app = create_app()

with app.app_context():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            print("\n--- RECRUITERS ---")
            cursor.execute("SELECT recruiter_id, company_email, company_name FROM recruiters")
            recruiters = cursor.fetchall()
            for r in recruiters:
                print(r)
                
            print("\n--- JOBS (Latest 5) ---")
            cursor.execute("SELECT job_id, recruiter_id, title FROM jobs ORDER BY posted_at DESC LIMIT 5")
            jobs = cursor.fetchall()
            for j in jobs:
                print(j)

            print("\n--- INTERNSHIPS (Latest 5) ---")
            cursor.execute("SELECT internship_id, recruiter_id, title FROM internships ORDER BY posted_at DESC LIMIT 5")
            internships = cursor.fetchall()
            for i in internships:
                print(i)
                
            print("\n--- APPLICATIONS (Latest 5) ---")
            cursor.execute("SELECT application_id, item_type, item_id, user_id, status FROM applications ORDER BY applied_at DESC LIMIT 5")
            apps = cursor.fetchall()
            for a in apps:
                print(a)
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
