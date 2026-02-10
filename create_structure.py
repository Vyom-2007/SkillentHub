import os

base_dir = r"c:\SkillentHub\app"
blueprints = [
    "auth", "recruiter_auth", 
    "profile", "recruiter_profile",
    "feed", "posts", 
    "network", "connections", 
    "messages", "notifications", 
    "jobs", "competitions", 
    "teams", "applications", 
    "settings", "recruiter_dashboard", 
    "recruiter_jobs", "recruiter_competitions", 
    "recruiter_applications", "recruiter_settings"
]

utils = ["validators.py", "decorators.py", "helpers.py", "constants.py", "errors.py"]

def create_structure():
    # Create blueprints
    bp_dir = os.path.join(base_dir, "blueprints")
    if not os.path.exists(bp_dir):
        os.makedirs(bp_dir)
        
    for bp in blueprints:
        path = os.path.join(bp_dir, bp)
        if not os.path.exists(path):
            os.makedirs(path)
        
        # Create __init__.py
        with open(os.path.join(path, "__init__.py"), "w") as f:
            f.write(f"from flask import Blueprint\n\n{bp}_bp = Blueprint('{bp}', __name__)\n\nfrom . import routes\n")
            
        # Create routes.py
        with open(os.path.join(path, "routes.py"), "w") as f:
            f.write(f"from flask import render_template\nfrom . import {bp}_bp\n\n")

    # Create utils
    utils_dir = os.path.join(base_dir, "utils")
    if not os.path.exists(utils_dir):
        os.makedirs(utils_dir)
        
    for util in utils:
        with open(os.path.join(utils_dir, util), "w") as f:
            if util == "__init__.py":
                pass
            else:
                f.write(f"# {util}\n")

if __name__ == "__main__":
    create_structure()
    print("Structure created.")
