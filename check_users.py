
from app import create_app
from database.db import execute_query

app = create_app()
ctx = app.app_context()
ctx.push()

users = execute_query("SELECT id, full_name, email FROM users", fetch_all=True)
print(f"Total Users: {len(users)}")
for user in users:
    print(user)
