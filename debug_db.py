from app import create_app
from app.database.connection import execute_query

app = create_app()

with app.app_context():
    print("--- Users ---")
    users = execute_query("SELECT user_id, email FROM users LIMIT 5", fetch_all=True)
    for u in users:
        print(u)
        
    print("\n--- Recruiters ---")
    recruiters = execute_query("SELECT recruiter_id, company_email FROM recruiters LIMIT 5", fetch_all=True)
    for r in recruiters:
        print(r)
