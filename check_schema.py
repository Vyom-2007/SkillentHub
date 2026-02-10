
import sys
import os
from app.database.connection import execute_query
from app import create_app

sys.path.append(os.getcwd())

def check_schema():
    app = create_app('development')
    with app.app_context():
        print("Checking hackathon_registrations schema...")
        cols = execute_query("DESCRIBE hackathon_registrations", fetch_all=True)
        for c in cols:
            print(f"{c['Field']} - {c['Type']}")

if __name__ == "__main__":
    check_schema()
