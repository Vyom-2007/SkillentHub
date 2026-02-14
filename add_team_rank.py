import sys
import os
from flask import Flask

sys.path.append(os.getcwd())
try:
    from app import create_app
    from app.database.connection import execute_update, execute_query
except ImportError:
    pass

app = create_app()

def add_rank_column():
    print("Checking teams table schema...")
    try:
        cols = execute_query("DESCRIBE teams", fetch_all=True)
        has_rank = any(c['Field'] == 'rank' for c in cols)
        
        if not has_rank:
            print("Adding 'rank' column to teams table...")
            # Try simpler syntax if previous failed, though standard MySQL is ADD COLUMN
            # Maybe the error was about something else. Let's try to catch full error.
            try:
                execute_update("ALTER TABLE teams ADD COLUMN `rank` VARCHAR(50) DEFAULT NULL", ())
                print("Column 'rank' added successfully.")
            except Exception as e:
                print(f"Failed with ADD COLUMN: {e}")
                # Try ADD without COLUMN keyword (older mysql versions sometimes weird, but unlikely)
                # Actually, check if it's reserved word? 'rank' is reserved in MySQL 8.0.2+ as window function.
                # So we MUST quote it.
                execute_update("ALTER TABLE teams ADD `rank` VARCHAR(50) DEFAULT NULL", ())
                print("Column `rank` added successfully (quoted).")

        else:
            print("'rank' column already exists.")
            
    except Exception as e:
        print(f"Error updating schema: {e}")

if __name__ == '__main__':
    with app.app_context():
        add_rank_column()
