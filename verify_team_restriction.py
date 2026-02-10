
import sys
import os
from flask import Flask

sys.path.append(os.getcwd())

from app import create_app
from app.services.event_service import register_hackathon
from app.database.connection import execute_insert, execute_query

def verify_restriction():
    app = create_app('development')
    app.config['TESTING'] = True
    
    with app.app_context():
        # Setup
        print("Setting up test data...")
        rid = 1
        hid = execute_insert(
            "INSERT INTO hackathons (recruiter_id, title, start_date, end_date, is_active, team_size) VALUES (%s, 'Restriction Test', NOW(), NOW() + INTERVAL 2 DAY, 1, 5)", 
            (rid,)
        )
        
        # User 1 (Leader)
        lead_id = 1 
        
        # Existing User (Member)
        # Create a dummy user
        mem_email = "existing_member@test.com"
        mem_id = execute_insert("INSERT INTO users (email, password_hash, is_active) VALUES (%s, 'hash', 1)", (mem_email,))
        execute_insert("INSERT INTO profiles (user_id, full_name) VALUES (%s, 'Existing Member')", (mem_id,))
        
        # Non-Existent User (Member)
        fake_email = "ghost_user@test.com"
        
        try:
            members = [
                {'email': mem_email, 'name': 'Existing User'},
                {'email': fake_email, 'name': 'Ghost User'}
            ]
            
            print(f"Attempting to register team with one non-existent user: {fake_email}")
            success, msg = register_hackathon(hid, lead_id, team_name="TestTeam", members=members)
            
            print(f"Result: Success={success}, Msg='{msg}'")
            
            if success:
                print("FAIL: Registration succeeded but should have failed due to non-existent user.")
            else:
                if "not registered" in msg.lower() or "must be registered" in msg.lower():
                     print("SUCCESS: Registration failed as expected.")
                else:
                     print(f"FAIL: Registration failed but with unexpected message: {msg}")

            # 2. Success Case
            print("\nAttempting VALID registration with existing users...")
            valid_members = [
                {'email': mem_email, 'name': 'Existing User'} 
                # lead_id is also a member implicitly? No, usually separate.
            ]
            success, msg = register_hackathon(hid, lead_id, team_name="ValidTeam", members=valid_members)
            print(f"Result: Success={success}, Msg='{msg}'")
            
            if success:
                print("SUCCESS: Valid registration succeeded.")
            else:
                print(f"FAIL: Valid registration failed: {msg}")

        finally:
            print("Cleaning up...")
            execute_query("DELETE FROM hackathon_registrations WHERE hackathon_id = %s", (hid,))
            execute_query("DELETE FROM team_members WHERE team_id IN (SELECT team_id FROM teams WHERE item_id = %s)", (hid,))
            execute_query("DELETE FROM teams WHERE item_id = %s", (hid,))
            execute_query("DELETE FROM hackathons WHERE hackathon_id = %s", (hid,))
            execute_query("DELETE FROM profiles WHERE user_id = %s", (mem_id,))
            execute_query("DELETE FROM users WHERE user_id = %s", (mem_id,))

if __name__ == "__main__":
    verify_restriction()
