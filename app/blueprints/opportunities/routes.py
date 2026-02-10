from flask import Blueprint, render_template, session, redirect, url_for

opportunities_bp = Blueprint('opportunities', __name__, url_prefix='/opportunities')

@opportunities_bp.route('/')
def index():
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    
    # Placeholder data for opportunities/competitions
    opportunities = [
        {
            'id': 1,
            'title': 'HackMIT 2024',
            'organization': 'MIT',
            'description': 'One of the largest undergraduate hackathons.',
            'date': 'Sep 15, 2024',
            'link': '#'
        },
        {
            'id': 2,
            'title': 'Google Summer of Code',
            'organization': 'Google',
            'description': 'Global program focused on bringing more student developers into open source software development.',
            'date': 'Applications Open Soon',
            'link': '#'
        },
        {
            'id': 3,
            'title': 'Smart India Hackathon',
            'organization': 'Government of India',
            'description': 'Nationwide initiative to provide students a platform to solve some of the pressing problems.',
            'date': 'Oct 2024',
            'link': '#'
        }
    ]
    
    return render_template('opportunities/index.html', opportunities=opportunities)
