import sys
import os
from flask import Flask

sys.path.append(os.getcwd())
try:
    from app import create_app
    from app.database.connection import execute_query
except ImportError:
    pass

app = create_app()

def inspect_teams():
    print("Inspecting teams table schema...", flush=True)
    try:
        cols = execute_query("DESCRIBE teams", fetch_all=True)
        for col in cols:
            print(f"  {col['Field']} ({col['Type']})", flush=True)
            
    except Exception as e:
        print(f"Error inspecting schema: {e}", flush=True)

if __name__ == '__main__':
    with app.app_context():
        inspect_teams()
