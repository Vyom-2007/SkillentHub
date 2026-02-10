
import sys
import os
from app.database.connection import execute_query
from app import create_app

sys.path.append(os.getcwd())

def check_orphans():
    app = create_app('development')
    with app.app_context():
        print("Checking for orphans...")
        
        query = """
            SELECT hr.user_id, hr.hackathon_id 
            FROM hackathon_registrations hr
            LEFT JOIN users u ON hr.user_id = u.user_id
            WHERE u.user_id IS NULL
        """
        orphans = execute_query(query, fetch_all=True)
        if orphans:
            print(f"Found {len(orphans)} orphans in hackathon_registrations:")
            for o in orphans:
                print(o)
        else:
            print("No orphans found.")

if __name__ == "__main__":
    check_orphans()
