import sys
import os
from flask import Flask, session

sys.path.append(os.getcwd())
try:
    from app import create_app
    from app.database.connection import execute_insert, execute_update, execute_query
    from app.services import profile_service
except ImportError:
    pass

app = create_app()

def verify_wins():
    print("Setting up wins verification...", flush=True)
    try:
        ctx = app.app_context()
        ctx.push()
        client = app.test_client()
        
        # Cleanup
        execute_update("DELETE FROM users WHERE email IN ('win_user@test.com', 'teammate@test.com')", ())
        execute_update("DELETE FROM competitions WHERE title = 'Win Comp'", ())
        
        # Create Users
        user_id = execute_insert("INSERT INTO users (email, password_hash, is_active) VALUES ('win_user@test.com', 'hash', 1)", ())
        execute_insert("INSERT INTO profiles (user_id, full_name, visibility) VALUES (%s, 'Winner User', 'public')", (user_id,))
        
        teammate_id = execute_insert("INSERT INTO users (email, password_hash, is_active) VALUES ('teammate@test.com', 'hash', 1)", ())
        execute_insert("INSERT INTO profiles (user_id, full_name) VALUES (%s, 'Teammate User')", (teammate_id,))
        
        # Create Competition
        comp_id = execute_insert("INSERT INTO competitions (title, start_date, end_date, is_active) VALUES ('Win Comp', NOW() - INTERVAL 5 DAY, NOW() - INTERVAL 1 DAY, 1)", ())
        
        # Create Winning Team
        # Note: 'rank' column is what we added.
        # teams table uses item_type/item_id instead of competition_id
        team_id = execute_insert("INSERT INTO teams (item_type, item_id, team_name, created_by, `rank`) VALUES ('competition', %s, 'The Champions', %s, '1st')", (comp_id, user_id))
        
        # Add Members
        execute_insert("INSERT INTO team_members (team_id, user_id, role) VALUES (%s, %s, 'leader')", (team_id, user_id))
        execute_insert("INSERT INTO team_members (team_id, user_id, role) VALUES (%s, %s, 'member')", (team_id, teammate_id))
        
        print(f"Created data: User={user_id}, Comp={comp_id}, Team={team_id} (Rank='1st')", flush=True)

        # Test Logic
        wins = profile_service.get_user_wins(user_id)
        print(f"\nFetched {len(wins)} wins directly from service.", flush=True)
        if len(wins) > 0:
            print(f"   Win: {wins[0]['rank']} Place in {wins[0]['event_title']}", flush=True)
            print(f"   Members: {[m['full_name'] for m in wins[0]['members']]}", flush=True)
        else:
            print("   FAIL: Service returned no wins.", flush=True)
            return

        # Test Page
        with client.session_transaction() as sess:
            sess['user_id'] = user_id
            
        print("\nRequesting profile page...", flush=True)
        resp = client.get(f'/profile/{user_id}', follow_redirects=True)
        content = resp.data.decode()
        
        if 'Achievements' in content and '1st Place' in content and 'Win Comp' in content and 'Teammate User' in content:
            print("   PASS: Profile page displays achievement and teammate correctly.", flush=True)
        else:
            print("   FAIL: Profile page missing achievement details.", flush=True)
            # print(content[:500])

    except Exception as e:
        print(f"ERROR: {e}", flush=True)
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    verify_wins()
