
import sys
import os
import traceback

# Add app to path
sys.path.append(os.getcwd())

from app import create_app
from app.services import recruiter_service
from app.database.connection import execute_query

def debug_dashboard():
    app = create_app('development')
    with app.app_context():
        print("Debugging Dashboard...")
        
        # Get a recruiter ID (Use the one from verify script if possible, or any)
        # Try to find a recruiter
        recruiter = execute_query("SELECT recruiter_id FROM recruiters LIMIT 1", fetch_one=True)
        if not recruiter:
            print("No recruiters found in DB.")
            return

        recruiter_id = recruiter['recruiter_id']
        print(f"Using Recruiter ID: {recruiter_id}")
        
        try:
            print("Calling get_dashboard_stats...")
            stats = recruiter_service.get_dashboard_stats(recruiter_id)
            print("Stats retrieved successfully.")
            print(stats)
        except Exception:
            print("Exception in get_dashboard_stats:")
            traceback.print_exc()
            
        try:
            print("\nCalling get_recent_applications...")
            apps = recruiter_service.get_recent_applications(recruiter_id)
            print("Recent apps retrieved successfully.")
            for a in apps:
                 print(a)
        except Exception:
            print("Exception in get_recent_applications:")
            traceback.print_exc()

if __name__ == "__main__":
    debug_dashboard()
