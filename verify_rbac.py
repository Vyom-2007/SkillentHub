
import os
import sys
from app import create_app
from app.database.connection import execute_query, execute_insert, get_db_connection
from app.services import recruiter_manage_service, application_service, auth_service
from app.models import recruiter as recruiter_model
import bcrypt

app = create_app()

def run_rbac_verification():
    with app.app_context():
        print("Starting RBAC Verification...")
        
        # 1. Setup Test Recruiters
        print("\n--- Setting up Recruiters ---")
        # Helper to get/create recruiter
        def get_or_create_recruiter(name, email):
            r = recruiter_model.get_by_email(email)
            if not r:
                pw_hash = bcrypt.hashpw('password'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                rid, _ = recruiter_model.create(name, email, pw_hash)
                return rid
            return r['recruiter_id']

        r1_id = get_or_create_recruiter("Recruiter One", "r1@test.com")
        r2_id = get_or_create_recruiter("Recruiter Two", "r2@test.com")
        print(f"Recruiter 1 ID: {r1_id}")
        print(f"Recruiter 2 ID: {r2_id}")

        # 2. Setup Test Job for R1
        print("\n--- Setting up Job ---")
        job_title = "RBAC Test Job"
        # Check if job exists
        job = execute_query("SELECT job_id FROM jobs WHERE recruiter_id=%s AND title=%s", (r1_id, job_title), fetch_one=True)
        if not job:
            query = """
                INSERT INTO jobs (recruiter_id, title, description, location, job_type, salary_range, posted_at, is_active)
                VALUES (%s, %s, 'Desc', 'Remote', 'Full-time', '100k', NOW(), 1)
            """
            job_id = execute_insert(query, (r1_id, job_title))
        else:
            job_id = job['job_id']
        print(f"Job ID: {job_id} (Owned by Recruiter 1)")

        # 3. Setup User Application
        print("\n--- Setting up Application ---")
        user = execute_query("SELECT user_id FROM users LIMIT 1", fetch_one=True)
        user_id = user['user_id']
        
        # Apply if not exists
        app_check = execute_query("SELECT application_id FROM applications WHERE user_id=%s AND item_type='job' AND item_id=%s", (user_id, job_id), fetch_one=True)
        if not app_check:
            # We need a resume path, dummy one
            app_id, _ = application_service.apply_to_opportunity(user_id, 'job', job_id, None, "Cover letter") 
            # Note: apply_to_opportunity might fail if resume is None and it validates. 
            # Re-reading apply_to_opportunity... it takes `resume` file object. 
            # Let's bypass service and insert directly for test to avoid file upload logic complexity in script
            query = "INSERT INTO applications (user_id, item_type, item_id, resume_path, cover_letter, status) VALUES (%s, 'job', %s, 'dummy.pdf', 'cover', 'applied')"
            app_id = execute_insert(query, (user_id, job_id))
        else:
            app_id = app_check['application_id']
        print(f"Application ID: {app_id}")

        # 4. Test UNAUTHORIZED Access (Recruiter 2)
        print("\n--- Testing UNAUTHORIZED Access (Recruiter 2 performing actions on R1's app) ---")
        
        # Test Status Update
        print("1. Testing Status Update...")
        success, msg = recruiter_manage_service.update_application_status(app_id, 'reviewing', recruiter_id=r2_id)
        print(f"   Result: Success={success}, Message='{msg}'")
        if not success and "Unauthorized" in msg:
            print("   [PASS] Unauthorized access blocked.")
        else:
            print("   [FAIL] Unauthorized access NOT blocked!")

        # Test Add Note
        print("2. Testing Add Note...")
        success = recruiter_manage_service.add_note(app_id, r2_id, "Malicious note")
        print(f"   Result: Success={success}")
        if not success:
            print("   [PASS] Unauthorized note addition blocked.")
        else:
             print("   [FAIL] Unauthorized note addition succeeded!")

        # 5. Test AUTHORIZED Access (Recruiter 1)
        print("\n--- Testing AUTHORIZED Access (Recruiter 1) ---")
        
        # Test Status Update
        print("1. Testing Status Update...")
        success, msg = recruiter_manage_service.update_application_status(app_id, 'reviewing', recruiter_id=r1_id)
        print(f"   Result: Success={success}, Message='{msg}'")
        if success:
             print("   [PASS] Authorized access allowed.")
        else:
             print(f"   [FAIL] Authorized access failed: {msg}")

        # Test Add Note
        print("2. Testing Add Note...")
        success = recruiter_manage_service.add_note(app_id, r1_id, "Legit note")
        print(f"   Result: Success={success}")
        if success:
             print("   [PASS] Authorized note addition allowed.")
        else:
             print("   [FAIL] Authorized note addition failed.")

if __name__ == "__main__":
    run_rbac_verification()
