
import sys
import os
import traceback
from flask import Flask, render_template

# Add app to path
sys.path.append(os.getcwd())

from app import create_app

def reproduce_error():
    app = create_app('development')
    with app.test_request_context('/recruiter/login', method='GET'):
        try:
            print("Rendering login template...")
            # Simulate what the route probably does (we'll confirm after viewing routes.py)
            # If routes.py doesn't pass 'email', this might trigger the error if strict
            output = render_template('recruiter/login.html')
            print("Render successful.")
        except Exception:
            print("Exception during render:")
            traceback.print_exc()

if __name__ == "__main__":
    reproduce_error()
