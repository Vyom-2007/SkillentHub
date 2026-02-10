from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from app.models.job import Job
from app.models.internship import Internship
from app.models.competition import Competition
from app.models.application import Application
from app.services.file_service import save_resume
from app.utils.decorators import login_required

jobs_bp = Blueprint('jobs', __name__)

@jobs_bp.route('/')
@login_required
def index():
    search = request.args.get('q')
    filters = {'search': search} if search else None
    
    jobs = Job.get_all(filters)
    internships = Internship.get_all(filters)
    competitions = Competition.get_all(filters)
    
    # Merge and sort by posted_at desc
    # Both have 'posted_at'
    all_items = []
    for j in jobs:
        j['type'] = 'Job'
        all_items.append(j)
    for i in internships:
        i['type'] = 'Internship'
        all_items.append(i)
    for c in competitions:
        c['type'] = 'Competition'
        all_items.append(c)
        
    all_items.sort(key=lambda x: x['posted_at'], reverse=True)
    
    return render_template('jobs/index.html', items=all_items, search=search)

@jobs_bp.route('/<string:type>/<int:id>')
@login_required
def detail(type, id):
    if type == 'job':
        item = Job.get_by_id(id)
    elif type == 'internship':
        item = Internship.get_by_id(id)
    elif type == 'competition':
        item = Competition.get_by_id(id) # Need to ensure model has get_by_id. Yes, assume standard.
        # Wait, I didn't verify Competition.get_by_id exists in model creation step.
        # I did create get_all. I missed get_by_id in Competition model creation tool call.
        # I MUST fix Competition model first or now.
        # I'll add get_by_id to Competition model in next tool call.
    else:
        return redirect(url_for('jobs.index'))
        
    if not item:
        flash('Item not found', 'danger')
        return redirect(url_for('jobs.index'))
        
    item['type'] = type # 'job' or 'internship'
    return render_template('jobs/detail.html', item=item)

@jobs_bp.route('/apply/<string:type>/<int:id>', methods=['POST'])
@login_required
def apply(type, id):
    user_id = session['user_id']
    cover_letter = request.form.get('cover_letter')
    resume_option = request.form.get('resume_option') # 'existing' or 'upload'
    
    resume_path = None
    
    if resume_option == 'upload':
        file = request.files.get('resume')
        if file and file.filename != '':
            resume_path = save_resume(file, user_id)
    elif resume_option == 'existing':
        # Get from profile
        from app.models.profile import Profile
        p = Profile.get_by_user_id(user_id)
        resume_path = p['resume_path']
        
    if not resume_path:
        flash('Resume required', 'danger')
        return redirect(url_for('jobs.detail', type=type, id=id))
        
    data = {
        'user_id': user_id,
        'item_type': type, # 'job' or 'internship' (matches table names singular? No, tables are plural 'jobs', 'internships'. Application calls it item_type. Let's stick to 'job'/'internship' strings locally, ensure DB consistent.)
        # Application model checks 'item_type'. Let's verify schema.
        # Table applications: item_type ENUM('job','internship','competition','hackathon'). Singular.
        'item_id': id,
        'resume_path': resume_path,
        'cover_letter': cover_letter
    }
    
    res = Application.create(data)
    if res is False:
        flash('You have already applied to this.', 'warning')
    else:
        flash('Application submitted successfully!', 'success')
        
    return redirect(url_for('jobs.detail', type=type, id=id))
