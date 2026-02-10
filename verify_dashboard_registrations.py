
import sys
import os
from datetime import datetime

# Add app to path
sys.path.append(os.getcwd())

from app import create_app
from app.database.connection import execute_query, execute_insert
from app.services import recruiter_service

def verify_dashboard_registrations():
    app = create_app('development')
    with app.app_context():
        print("Setting up test data for Dashboard Verification...")
        
        # 1. Create Test Recruiter
        rec_email = f"dash_rec_{int(datetime.now().timestamp())}@example.com"
        execute_insert("INSERT INTO recruiters (company_email, password_hash, company_name) VALUES (%s, 'hash', 'Dash Company')", (rec_email,))
        rec_id = execute_query("SELECT recruiter_id FROM recruiters WHERE company_email=%s", (rec_email,), fetch_one=True)['recruiter_id']
        print(f"Created Recruiter ID: {rec_id}")

        # 2. Create Test User
        user_email = f"dash_user_{int(datetime.now().timestamp())}@example.com"
        execute_insert("INSERT INTO users (email, password_hash) VALUES (%s, 'hash')", (user_email,))
        user_id = execute_query("SELECT user_id FROM users WHERE email=%s", (user_email,), fetch_one=True)['user_id']
        execute_insert("INSERT INTO profiles (user_id, full_name, visibility) VALUES (%s, 'Dash Candidate', 'public')", (user_id,))
        print(f"Created User ID: {user_id}")

        # 3. Create Hackathon & Register User
        execute_insert("INSERT INTO hackathons (recruiter_id, title, description, start_date, end_date, venue, mode) VALUES (%s, 'Dash Hackathon', 'Desc', NOW(), NOW(), 'Venue', 'online')", (rec_id,))
        hack_id = execute_query("SELECT hackathon_id FROM hackathons WHERE recruiter_id=%s ORDER BY hackathon_id DESC LIMIT 1", (rec_id,), fetch_one=True)['hackathon_id']
        
        execute_insert("INSERT INTO hackathon_registrations (hackathon_id, user_id) VALUES (%s, %s)", (hack_id, user_id))
        print(f"Registered User {user_id} to Hackathon {hack_id}")

        # 4. Create Job & Apply User
        execute_insert("INSERT INTO jobs (recruiter_id, title, location, job_type, description) VALUES (%s, 'Dash Job', 'Loc', 'full-time', 'Desc')", (rec_id,))
        job_id = execute_query("SELECT job_id FROM jobs WHERE recruiter_id=%s ORDER BY job_id DESC LIMIT 1", (rec_id,), fetch_one=True)['job_id']
        
        execute_insert("INSERT INTO applications (user_id, item_type, item_id, status) VALUES (%s, 'job', %s, 'applied')", (user_id, job_id))
        print(f"Applied User {user_id} to Job {job_id}")

        # 5. Verify Dashboard Stats
        print("\nVerifying Dashboard Stats...")
        stats = recruiter_service.get_dashboard_stats(rec_id)
        
        print(f"Total Applications: {stats['total_applications']}")
        if stats['total_applications'] == 2:
            print("PASSED: Total count is 2 (1 Job App + 1 Hackathon Reg)")
        else:
            print(f"FAILED: Total count mismatch. Expected 2, got {stats['total_applications']}")

        # 6. Verify Recent Applications List
        print("\nVerifying Recent Activity List...")
        recent = recruiter_service.get_recent_applications(rec_id)
        
        found_job = False
        found_hack = False
        
        for item in recent:
            print(f"- {item['item_type']}: {item['item_title']} ({item['candidate_name']})")
            if item['item_type'] == 'job' and item['item_id'] == job_id:
                found_job = True
            if item['item_type'] == 'hackathon' and item['item_id'] == hack_id:
                found_hack = True
                
        if found_job and found_hack:
            print("PASSED: Both Job Application and Hackathon Registration found in list.")
        else:
            print(f"FAILED: Missing items. Job: {found_job}, Hack: {found_hack}")

if __name__ == "__main__":
    verify_dashboard_registrations()
