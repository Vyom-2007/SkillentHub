
import sys
import os
import traceback
from flask import Flask, render_template

# Add app to path
sys.path.append(os.getcwd())

from app import create_app

def reproduce_error():
    app = create_app('development')
    app.config['TESTING'] = True
    app.config['DEBUG'] = True
    client = app.test_client()
    
    try:
        print("Requesting /recruiter/login...")
        response = client.get('/recruiter/login')
        print(f"Status Code: {response.status_code}")
        if response.status_code == 500:
            print("Server Error Triggered!")
            # In debug mode, response.data might contain the traceback rendered as HTML
            # but getting the internal exception is harder without a signal listener
            # However, typical Flask debug output might show up in stderr/stdout
    except Exception:
        print("Exception during request:")
        traceback.print_exc()

if __name__ == "__main__":
    reproduce_error()
