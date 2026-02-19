import requests
import time
import sys
from bs4 import BeautifulSoup
import re

BASE_URL = "http://127.0.0.1:5000"
RECRUITER_EMAIL = f"recruiter_{int(time.time())}@example.com"
RECRUITER_PASSWORD = "Password123!"
CANDIDATE_EMAIL = f"candidate_{int(time.time())}@example.com"
CANDIDATE_PASSWORD = "Password123!"

def print_result(step, success, message=""):
    print(f"[{'PASS' if success else 'FAIL'}] {step}: {message}")
    if not success:
        sys.exit(1)

def main():
    recruiter_session = requests.Session()
    candidate_session = requests.Session()
    
    # 1. Register Recruiter
    print("\n--- 1. Register Recruiter ---")
    resp = recruiter_session.post(f"{BASE_URL}/recruiter/register", data={
        "company_name": "Test Corp",
        "email": RECRUITER_EMAIL,
        "password": RECRUITER_PASSWORD,
        "confirm_password": RECRUITER_PASSWORD,
        "phone": "1234567890",
        "website": "https://example.com"
    })
    print_result("Register Recruiter", resp.status_code == 200, f"Status: {resp.status_code}")

    # 2. Login Recruiter
    print("\n--- 2. Login Recruiter ---")
    resp = recruiter_session.post(f"{BASE_URL}/recruiter/login", data={
        "email": RECRUITER_EMAIL,
        "password": RECRUITER_PASSWORD
    })
    print_result("Login Recruiter", "Dashboard" in resp.text or resp.url.endswith('/recruiter/dashboard'), "Logged in")

    # 3. Post Job
    print("\n--- 3. Post Job ---")
    job_title = f"Test Job {int(time.time())}"
    job_data = {
        "title": job_title,
        "location": "Remote",
        "job_type": "full-time",
        "work_mode": "remote",
        "experience_required": "0-1",
        "skills_required": "Python, Flask",
        "salary_range": "$100k",
        "description": "This is a test job description.",
        "requirements": "Must know Python.",
        "openings": 1,
        "deadline": "2026-12-31"
    }
    resp = recruiter_session.post(f"{BASE_URL}/recruiter/jobs/create", data=job_data)
    print_result("Post Job", "Job posted successfully" in resp.text, "Job Posted")

    # 4. Post Internship
    print("\n--- 4. Post Internship ---")
    internship_title = f"Test Internship {int(time.time())}"
    internship_data = {
        "title": internship_title,
        "location": "Remote",
        "duration": "3 months",
        "stipend": "10000",
        "work_mode": "remote",
        "skills_required": "Python",
        "description": "Test Internship",
        "requirements": "Basic Python",
        "deadline": "2026-12-31",
        "certificate_provided": "on"
    }
    resp = recruiter_session.post(f"{BASE_URL}/recruiter/internships/create", data=internship_data)
    print_result("Post Internship", "Internship posted successfully" in resp.text, "Internship Posted")

    # 5. Post Competition
    print("\n--- 5. Post Competition ---")
    competition_title = f"Test Competition {int(time.time())}"
    comp_data = {
        "title": competition_title,
        "description": "Test Competition Desc",
        "rules": "No cheating",
        "start_date": "2026-06-01T10:00",
        "end_date": "2026-06-02T10:00",
        "prize_details": "iphone",
        "max_participants": 100,
        "registration_deadline": "2026-05-30"
    }
    resp = recruiter_session.post(f"{BASE_URL}/recruiter/competitions/create", data=comp_data)
    print_result("Post Competition", "Competition created successfully" in resp.text, "Competition Posted")

    # 6. Post Hackathon
    print("\n--- 6. Post Hackathon ---")
    hackathon_title = f"Test Hackathon {int(time.time())}"
    hack_data = {
        "title": hackathon_title,
        "description": "Hackathon Desc",
        "theme": "AI",
        "start_date": "2026-07-01T10:00",
        "end_date": "2026-07-03T10:00",
        "venue": "Virtual",
        "mode": "online",
        "team_size": "2-4",
        "team_size_max": 4,
        "prize_details": "Cash",
        "registration_deadline": "2026-06-30"
    }
    resp = recruiter_session.post(f"{BASE_URL}/recruiter/hackathons/create", data=hack_data)
    print_result("Post Hackathon", "Hackathon created successfully" in resp.text, "Hackathon Posted")

    # 7. Register Candidate
    print("\n--- 7. Register Candidate ---")
    resp = candidate_session.post(f"{BASE_URL}/register", data={
        "full_name": "Test Candidate",
        "email": CANDIDATE_EMAIL,
        "password": CANDIDATE_PASSWORD,
        "confirm_password": CANDIDATE_PASSWORD
    })
    print_result("Register Candidate", resp.status_code == 200, f"Status: {resp.status_code}")

    # 8. Login Candidate
    print("\n--- 8. Login Candidate ---")
    resp = candidate_session.post(f"{BASE_URL}/login", data={
        "email": CANDIDATE_EMAIL,
        "password": CANDIDATE_PASSWORD
    })
    print_result("Login Candidate", "Dashboard" in resp.text, "Logged in")

    # 9. Find Items to Save (Search by title to get IDs)
    print("\n--- 9. Find and Save Items ---")
    
    def find_and_save(search_url, title_query, type_str):
        # Search page usually lists items. We can find the one with our title.
        # For jobs/internships: /api/opportunities/search
        # For comp/hack: /competitions or /hackathons list page
        
        item_id = None
        
        if type_str in ['job', 'internship']:
            resp = candidate_session.get(f"{BASE_URL}/api/opportunities/search?q={title_query}&type={type_str}")
            data = resp.json()
            if data['opportunities']:
                item_id = data['opportunities'][0]['id']
        else:
            # Parse list page
            list_url = f"{BASE_URL}/{type_str}s"
            resp = candidate_session.get(list_url)
            # Regex to find link with title: <a href="/competitions/(\d+)">...title...</a>
            # Using simple regex assuming title is distinct
            # Search for the link that contains the title
            # Example: <a href="/competitions/5" ...>Test Competition...</a>
            # We want the ID 5.
            # Let's find the position of the title, then look backward for href="/type/id"
            
            # Better: split by lines or standard soup
            try:
                soup = BeautifulSoup(resp.text, 'html.parser')
                # Find the h5 with the title
                title_tag = soup.find('h5', string=re.compile(re.escape(title_query)))
                if title_tag:
                    # Find parent card
                    card = title_tag.find_parent('div', class_='event-card')
                    if card:
                        # Find link in card
                        # Pattern /competitions/<id> or /hackathons/<id>
                        link = card.find('a', href=re.compile(f"/{type_str}s/(\d+)"))
                        if link:
                            href = link.get('href')
                            match = re.search(r'/(\d+)', href)
                            if match:
                                item_id = match.group(1)
            except Exception as e:
                print(f"Error parsing HTML: {e}")

        if item_id:
            print(f"Found {type_str} ID: {item_id}")
            # Save it
            save_resp = candidate_session.post(f"{BASE_URL}/opportunities/save/{type_str}/{item_id}")
            if save_resp.json().get('success'):
                print(f"Saved {type_str}")
                return True
            else:
                print(f"Failed to save {type_str}")
                return False
        else:
            print(f"Could not find {type_str}: {title_query}")
            return False

    success_job = find_and_save(None, job_title, 'job')
    success_intern = find_and_save(None, internship_title, 'internship')
    success_comp = find_and_save(None, competition_title, 'competition')
    success_hack = find_and_save(None, hackathon_title, 'hackathon')

    print_result("Save Items", success_job and success_intern and success_comp and success_hack, "All items saved")

    # 10. Verify Saved Items Page
    print("\n--- 10. Verify Saved Items Page ---")
    resp = candidate_session.get(f"{BASE_URL}/saved-jobs")
    page_content = resp.text
    
    missing = []
    if job_title not in page_content: missing.append("Job")
    if internship_title not in page_content: missing.append("Internship")
    if competition_title not in page_content: missing.append("Competition")
    if hackathon_title not in page_content: missing.append("Hackathon")
    
    if not missing:
        print_result("Verify Saved Page", True, "All titles found on saved page")
    else:
        print_result("Verify Saved Page", False, f"Missing titles: {missing}")

    print("\n--- FULL VERIFICATION COMPLETE ---")

if __name__ == "__main__":
    main()
