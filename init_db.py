import pymysql
from config import Config
import os

def init_db():
    print("Initializing Database...")
    
    # Connect without database first to create it if not exists
    try:
        conn = pymysql.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        
        # Read schema file
        with open('database/schema.sql', 'r', encoding='utf-8') as f:
            schema_sql = f.read()
            
        # Execute schema commands
        # Split by semicolon but ignore semicolons inside comments/strings if possible
        # For simplicity in this script, we'll try to split by ";\n" or execute mostly as block if supported, 
        # but pymysql doesn't support multi-statements by default unless enabled.
        # However, checking schema.sql, IT HAS 'DELIMITER' issues often.
        # But our schema is simple.
        
        # Let's execute statement by statement
        statements = schema_sql.split(';')
        
        # Create DB if needed
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DB} DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.execute(f"USE {Config.MYSQL_DB}")
        
        print(f"Using database: {Config.MYSQL_DB}")
        
        for statement in statements:
            if statement.strip():
                try:
                    cursor.execute(statement)
                except Exception as e:
                    # Ignore empty statements or comments causing errors if any
                    # specifically specific SET commands might fail on some cheap hosts but here straightforward
                    pass
        
        # Seed Skills
        print("Seeding skills...")
        with open('database/seed_skills.sql', 'r', encoding='utf-8') as f:
            seed_sql = f.read()
            seed_statements = seed_sql.split(';')
            for statement in seed_statements:
                if statement.strip():
                     try:
                        cursor.execute(statement)
                     except Exception as e:
                        pass # Duplicate entries
                        
        conn.commit()
        print("Database initialized successfully!")
        
    except Exception as e:
        print(f"Database initialization failed: {e}")
    finally:
        if 'conn' in locals() and conn.open:
            conn.close()

if __name__ == '__main__':
    init_db()
