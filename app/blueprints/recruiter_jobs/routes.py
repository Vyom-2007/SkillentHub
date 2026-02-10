from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models.job import Job
from app.models.internship import Internship
from app.models.competition import Competition
from app.utils.decorators import recruiter_login_required

recruiter_jobs_bp = Blueprint('recruiter_jobs', __name__)

@recruiter_jobs_bp.route('/')
@recruiter_login_required
def index():
    recruiter_id = session['recruiter_id']
    # Get jobs and internships
    jobs = Job.get_by_recruiter(recruiter_id)
    # Internships model needs get_by_recruiter too
    # Let's add it or use get_all with filter?
    # I'll add a quick method or raw sql here for speed if model missing
    # Checking previous file... Internship model only has get_all and get_by_id.
    # Missing get_by_recruiter. I will implement it here inline or update model later.
    # Inline for now to save tool calls.
    from app.database.connection import get_db
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM internships WHERE recruiter_id = %s ORDER BY posted_at DESC", (recruiter_id,))
    internships = cursor.fetchall()
    
    cursor.execute("SELECT * FROM competitions WHERE recruiter_id = %s ORDER BY posted_at DESC", (recruiter_id,))
    competitions = cursor.fetchall()
    cursor.close()
    
    return render_template('recruiter/jobs/index.html', jobs=jobs, internships=internships, competitions=competitions)

@recruiter_jobs_bp.route('/create', methods=['GET', 'POST'])
@recruiter_login_required
def create():
    if request.method == 'POST':
        type_ = request.form.get('type')
        data = request.form.to_dict()
        data['recruiter_id'] = session['recruiter_id']
        
        try:
            if type_ == 'job':
                Job.create(data)
                flash('Job posted successfully!', 'success')
            elif type_ == 'internship':
                Internship.create(data)
                flash('Internship posted successfully!', 'success')
            elif type_ == 'competition':
                Competition.create(data)
                flash('Competition posted successfully!', 'success')
            return redirect(url_for('recruiter_jobs.index'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
            
    return render_template('recruiter/jobs/create.html')
