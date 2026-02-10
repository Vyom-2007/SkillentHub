
import sys
import os
from flask import Flask

sys.path.append(os.getcwd())

from app import create_app
from app.database.connection import execute_query, execute_update

def fix_links():
    app = create_app('development')
    with app.app_context():
        print("--- Finding unlinked team members ---")
        # Find members with NULL user_id where email actually exists in users table
        query = """
            SELECT tm.member_id, tm.email, u.user_id 
            FROM team_members tm
            JOIN users u ON tm.email = u.email
            WHERE tm.user_id IS NULL
        """
        matches = execute_query(query, fetch_all=True)
        
        if not matches:
            print("No unlinked members found that match existing users.")
            return

        print(f"Found {len(matches)} members to link.")
        for m in matches:
            print(f"Linking member {m['member_id']} ({m['email']}) to user {m['user_id']}")
            update_sql = "UPDATE team_members SET user_id = %s WHERE member_id = %s"
            execute_update(update_sql, (m['user_id'], m['member_id']))
            
        print("Done.")

if __name__ == "__main__":
    fix_links()
