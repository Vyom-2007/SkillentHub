import sys
import os
from flask import Flask

# Add app directory to path
sys.path.append(os.getcwd())

from app import create_app
from app.services import recruiter_manage_service, application_service
from app.database.connection import execute_insert, execute_update, execute_query

app = create_app()

def test_full_auto_reject():
    print("Setting up test data...")
    try:
        # 1. Create Data
        u_id = execute_insert("INSERT INTO users (email, password_hash) VALUES ('full_test@example.com', 'hash')", ())
        r_id = execute_insert("INSERT INTO recruiters (company_name, company_email, password_hash) VALUES ('Full Corp', 'rec_full@example.com', 'hash')", ())
        
        # Create Opportunities
        j1_id = execute_insert("INSERT INTO jobs (recruiter_id, title) VALUES (%s, 'Job 1')", (r_id,))
        i1_id = execute_insert("INSERT INTO internships (recruiter_id, title, duration) VALUES (%s, 'Internship 1', '3 months')", (r_id,))
        c1_id = execute_insert("INSERT INTO competitions (recruiter_id, title) VALUES (%s, 'Comp 1')", (r_id,))
        
        # 2. Apply to All
        print("Applying to Job, Internship, and Competition...")
        app_j1 = execute_insert("INSERT INTO applications (user_id, item_type, item_id, status) VALUES (%s, 'job', %s, 'shortlisted')", (u_id, j1_id))
        app_i1 = execute_insert("INSERT INTO applications (user_id, item_type, item_id, status) VALUES (%s, 'internship', %s, 'reviewing')", (u_id, i1_id))
        app_c1 = execute_insert("INSERT INTO applications (user_id, item_type, item_id, status) VALUES (%s, 'competition', %s, 'registered')", (u_id, c1_id))
        
        # 3. Accept Job 1
        print("Recruiter accepting Job 1...")
        try:
            recruiter_manage_service.update_application_status(app_j1, 'accepted', r_id)
        except Exception as e:
            print(f"Service call exception (expected for email): {str(e)[:50]}...")

        # 4. Verify Statuses
        print("Verifying statuses...")
        
        # Job 1 should be accepted
        row_j1 = execute_query("SELECT status FROM applications WHERE application_id = %s", (app_j1,), fetch_one=True)
        if row_j1['status'] != 'accepted':
            print(f"FAILURE: Job 1 is {row_j1['status']}, expected 'accepted'")
        else:
            print("SUCCESS: Job 1 is accepted.")

        # Internship 1 should be rejected (Auto-reject works across types)
        row_i1 = execute_query("SELECT status FROM applications WHERE application_id = %s", (app_i1,), fetch_one=True)
        if row_i1['status'] != 'rejected':
            print(f"FAILURE: Internship 1 is {row_i1['status']}, expected 'rejected'")
        else:
            print("SUCCESS: Internship 1 is rejected.")

        # Competition 1 should stay registered
        row_c1 = execute_query("SELECT status FROM applications WHERE application_id = %s", (app_c1,), fetch_one=True)
        if row_c1['status'] != 'registered':
            print(f"FAILURE: Competition 1 is {row_c1['status']}, expected 'registered'")
        else:
            print("SUCCESS: Competition 1 is unchanged (registered).")

    except Exception as e:
        print(f"Test Failed: {e}")
    finally:
        # Clean up
        try:
            params = (u_id,)
            if 'u_id' in locals():
                execute_query("DELETE FROM applications WHERE user_id = %s", params)
                execute_query("DELETE FROM jobs WHERE recruiter_id = %s", (r_id,))
                execute_query("DELETE FROM internships WHERE recruiter_id = %s", (r_id,))
                execute_query("DELETE FROM competitions WHERE recruiter_id = %s", (r_id,))
                execute_update("DELETE FROM users WHERE user_id = %s", params)
                execute_update("DELETE FROM recruiters WHERE recruiter_id = %s", (r_id,))
        except:
            pass

if __name__ == '__main__':
    with app.app_context():
        test_full_auto_reject()
