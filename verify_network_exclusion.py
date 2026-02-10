
import sys
import os
import traceback
from flask import Flask

sys.path.append(os.getcwd())

from app import create_app
from app.services.network_service import get_all_users
from app.database.connection import execute_insert, execute_query

def verify_network_exclusion():
    app = create_app('development')
    app.config['TESTING'] = True
    
    with app.app_context():
        # 1. create dummy recruiter-user
        print("Creating dummy recruiter-user...")
        # Create user
        uid = execute_insert("INSERT INTO users (email, password_hash, is_active) VALUES ('rec_user_test@test.com', 'hash', 1)")
        # Create profile (so they WOULD show up if not for exclusion)
        execute_insert("INSERT INTO profiles (user_id, full_name, headline) VALUES (%s, 'Recruiter User', 'HR Manager')", (uid,))
        # Create recruiter entry
        execute_insert("INSERT INTO recruiters (user_id, company_name, company_email) VALUES (%s, 'TestCompany', 'hr@test.com')", (uid,))
        
        try:
            # 2. Fetch users
            print("Fetching network users...")
            result = get_all_users(current_user_id=999) # arbitrary ID
            users = result['users']
            
            # 3. Verify exclusion
            found = False
            for u in users:
                if u['user_id'] == uid:
                    found = True
                    print(f"FAIL: Found recruiter user {u['full_name']} (ID: {uid}) in network list!")
                    
            if not found:
                print("SUCCESS: Recruiter user correctly excluded from network.")
                
        finally:
            # Cleanup
            print("Cleaning up...")
            execute_query("DELETE FROM recruiters WHERE user_id = %s", (uid,))
            execute_query("DELETE FROM profiles WHERE user_id = %s", (uid,))
            execute_query("DELETE FROM users WHERE user_id = %s", (uid,))

if __name__ == "__main__":
    verify_network_exclusion()
