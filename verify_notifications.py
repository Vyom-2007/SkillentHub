
import os
import sys
from app import create_app
from app.database.connection import execute_query, execute_update, get_db_connection
from app.services import notification_service, connection_service, interview_service, message_service, team_service
import time

# Create app context
app = create_app()

def run_verification():
    with app.app_context():
        print("Starting Notification Verification...")
        
        # 1. Setup Test Users
        print("\n--- Setting up Test Data ---")
        # Ensure we have at least 2 users and 1 recruiter
        user1 = execute_query("SELECT user_id FROM users LIMIT 1", fetch_one=True)
        user2_query = "SELECT user_id FROM users WHERE user_id != %s LIMIT 1"
        user2 = execute_query(user2_query, (user1['user_id'],), fetch_one=True)
        
        recruiter = execute_query("SELECT recruiter_id FROM recruiters LIMIT 1", fetch_one=True)
        
        if not user1 or not user2 or not recruiter:
            print("Error: Need at least 2 users and 1 recruiter in DB.")
            return

        u1_id = user1['user_id']
        u2_id = user2['user_id']
        rec_id = recruiter['recruiter_id']
        
        print(f"User 1: {u1_id}, User 2: {u2_id}, Recruiter: {rec_id}")
        
        # Function to get latest notification
        def get_latest_notif(user_id):
            return execute_query(
                "SELECT * FROM notifications WHERE user_id = %s ORDER BY created_at DESC LIMIT 1",
                (user_id,), fetch_one=True
            )

        # 2. Test Connection Notification
        print("\n--- Testing Connection Notification ---")
        # Simulate request u1 -> u2
        notification_service.notify_connection_request(u1_id, u2_id)
        notif = get_latest_notif(u2_id)
        print(f"Connection Request Notif: Type={notif['type']}, Content='{notif['content']}'")
        assert notif['type'] == 'connection_request'
        
        # Simulate accept u2 -> u1
        notification_service.notify_connection_accepted(u2_id, u1_id)
        notif = get_latest_notif(u1_id)
        print(f"Connection Accepted Notif: Type={notif['type']}, Content='{notif['content']}'")
        assert notif['type'] == 'connection_accepted'

        # 3. Test Message Notification
        print("\n--- Testing Message Notification ---")
        notification_service.notify_new_message(u1_id, u2_id, 'user')
        notif = get_latest_notif(u2_id)
        print(f"Message Notif: Type={notif['type']}, Content='{notif['content']}'")
        assert notif['type'] == 'new_message'
        
        # 4. Test Interview Notification
        print("\n--- Testing Interview Notification ---")
        # Dummy interview ID
        notification_service.notify_interview_invite(rec_id, u1_id, 999, "2026-03-01 10:00:00")
        notif = get_latest_notif(u1_id)
        print(f"Interview Invite Notif: Type={notif['type']}, Content='{notif['content']}'")
        assert notif['type'] == 'interview_invite'
        
        notification_service.notify_interview_update(rec_id, u1_id, 999, "rescheduled")
        notif = get_latest_notif(u1_id)
        print(f"Interview Update Notif: Type={notif['type']}, Content='{notif['content']}'")
        assert notif['type'] == 'interview_update'

        # 5. Test Team Notification
        print("\n--- Testing Team Notification ---")
        notification_service.notify_team_invitation(u2_id, u1_id, "Test Team", 888)
        notif = get_latest_notif(u2_id)
        print(f"Team Invite Notif: Type={notif['type']}, Content='{notif['content']}'")
        assert notif['type'] == 'team_invitation'
        
        notification_service.notify_team_joined(u1_id, u2_id, "Test Team", 888)
        notif = get_latest_notif(u1_id)
        print(f"Team Joined Notif: Type={notif['type']}, Content='{notif['content']}'")
        assert notif['type'] == 'team_invitation_accepted'

        # 6. Test Application Update
        print("\n--- Testing Application Update ---")
        notification_service.notify_application_update(u1_id, "Software Engineer", "shortlisted", 777)
        notif = get_latest_notif(u1_id)
        print(f"App Update Notif: Type={notif['type']}, Content='{notif['content']}'")
        assert notif['type'] == 'application_update'
        
        print("\n--- Verification Completed Successfully ---")

if __name__ == "__main__":
    run_verification()
