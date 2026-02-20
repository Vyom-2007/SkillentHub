from app import create_app
from app.services import profile_service, recruiter_service, application_service
import sys
import traceback

app = create_app()

with open('debug_output.txt', 'w') as f:
    with app.app_context():
        f.write("--- Testing User Dashboard Service ---\n")
        try:
            user_id = 9 # Trying ID 9 which I saw in recruiter output
            f.write(f"Testing for user_id: {user_id}\n")
            
            # 1. Profile
            f.write("Calling get_profile_with_details...\n")
            profile = profile_service.get_profile_with_details(user_id)
            if profile:
                f.write(f"Profile found: {profile.get('full_name')}\n")
                f.write(f"Completion: {profile.get('completion')}%\n")
            else:
                f.write(f"Profile not found for user {user_id}\n")

            # 2. Applications
            f.write("Calling get_user_applications...\n")
            apps = application_service.get_user_applications(user_id, per_page=5)
            f.write(f"Applications found: {len(apps)}\n")
            
        except Exception as e:
            f.write(f"ERROR in User Dashboard: {e}\n")
            f.write(traceback.format_exc())

        f.write("\n--- Testing Recruiter Dashboard Service ---\n")
        try:
            recruiter_id = 9
            f.write(f"Testing for recruiter_id: {recruiter_id}\n")
            stats = recruiter_service.get_dashboard_stats(recruiter_id)
            f.write("Recruiter stats retrieved successfully\n")
            f.write(str(stats))
        except Exception as e:
            f.write(f"ERROR in Recruiter Dashboard: {e}\n")
            f.write(traceback.format_exc())
