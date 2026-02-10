from app import create_app
from app.database.connection import get_db_connection

app = create_app()

with app.app_context():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            print("--- R ---")
            cursor.execute("SELECT recruiter_id FROM recruiters")
            for r in cursor.fetchall():
                print(f"R: {r['recruiter_id']}")
                
            print("--- J ---")
            cursor.execute("SELECT job_id, recruiter_id FROM jobs")
            for j in cursor.fetchall():
                print(f"J: {j['job_id']} (Rec: {j['recruiter_id']})")
                
            print("--- A ---")
            cursor.execute("SELECT application_id, item_type, item_id, user_id FROM applications")
            for a in cursor.fetchall():
                print(f"A: {a['application_id']} ({a['item_type']} {a['item_id']}) User: {a['user_id']}")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
