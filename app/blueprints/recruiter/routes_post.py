"""
Recruiter routes for posting new opportunities.
"""
from flask import render_template, request, redirect, url_for, flash, session
from app.blueprints.recruiter.routes import recruiter_bp
from app.utils.decorators import recruiter_required
from app.services import recruiter_post_service

@recruiter_bp.route('/jobs/create', methods=['GET', 'POST'])
@recruiter_required
def create_job():
    if request.method == 'POST':
        recruiter_id = session.get('recruiter_id')
        data = {
            'title': request.form.get('title'),
            'location': request.form.get('location'),
            'job_type': request.form.get('job_type'),
            'work_mode': request.form.get('work_mode'),
            'experience_required': request.form.get('experience_required'),
            'skills_required': request.form.get('skills_required'),
            'salary_range': request.form.get('salary_range'),
            'description': request.form.get('description'),
            'requirements': request.form.get('requirements'),
            'openings': request.form.get('openings', 1),
            'deadline': request.form.get('deadline')
        }
        
        # Validation
        required_fields = ['title', 'location', 'job_type', 'work_mode', 'salary_range', 'description', 'openings', 'skills_required', 'deadline']
        if any(not data.get(k) for k in required_fields):
            flash('All fields marked with * are required.', 'danger')
            return render_template('recruiter/job_form.html')
        
        try:
            job_id = recruiter_post_service.create_job(recruiter_id, data)
            if job_id:
                flash('Job posted successfully!', 'success')
                return redirect(url_for('recruiter.dashboard'))
            else:
                flash('Failed to post job. Please try again.', 'danger')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
            
    return render_template('recruiter/job_form.html')

@recruiter_bp.route('/internships/create', methods=['GET', 'POST'])
@recruiter_required
def create_internship():
    if request.method == 'POST':
        recruiter_id = session.get('recruiter_id')
        data = {
            'title': request.form.get('title'),
            'location': request.form.get('location'),
            'duration': request.form.get('duration'),
            'stipend': request.form.get('stipend'),
            'work_mode': request.form.get('work_mode'),
            'certificate_provided': 'certificate_provided' in request.form,
            'skills_required': request.form.get('skills_required'),
            'description': request.form.get('description'),
            'requirements': request.form.get('requirements'),
            'deadline': request.form.get('deadline'),
            'openings': request.form.get('openings', 1)
        }

        # Validation
        required_fields = ['title', 'location', 'duration', 'stipend', 'work_mode', 'description', 'deadline', 'skills_required']
        if any(not data.get(k) for k in required_fields):
            flash('All fields marked with * are required.', 'danger')
            return render_template('recruiter/internship_form.html')
        
        try:
            internship_id = recruiter_post_service.create_internship(recruiter_id, data)
            if internship_id:
                flash('Internship posted successfully!', 'success')
                return redirect(url_for('recruiter.dashboard'))
            else:
                flash('Failed to post internship.', 'danger')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
            
    return render_template('recruiter/internship_form.html')

@recruiter_bp.route('/competitions/create', methods=['GET', 'POST'])
@recruiter_required
def create_competition():
    if request.method == 'POST':
        recruiter_id = session.get('recruiter_id')
        data = {
            'title': request.form.get('title'),
            'description': request.form.get('description'),
            'rules': request.form.get('rules'),
            'start_date': request.form.get('start_date'),
            'end_date': request.form.get('end_date'),
            'prize_details': request.form.get('prize_details'),
            'max_participants': request.form.get('max_participants'),
            'registration_deadline': request.form.get('registration_deadline')
        }

        # Validation
        required_fields = ['title', 'description', 'rules', 'start_date', 'end_date', 'prize_details', 'max_participants', 'registration_deadline']
        if any(not data.get(k) for k in required_fields):
            flash('All fields marked with * are required.', 'danger')
            return render_template('recruiter/competition_form.html')
        
        try:
            competition_id = recruiter_post_service.create_competition(recruiter_id, data)
            if competition_id:
                flash('Competition created successfully!', 'success')
                return redirect(url_for('recruiter.dashboard'))
            else:
                flash('Failed to create competition.', 'danger')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')

    return render_template('recruiter/competition_form.html')

@recruiter_bp.route('/hackathons/create', methods=['GET', 'POST'])
@recruiter_required
def create_hackathon():
    if request.method == 'POST':
        recruiter_id = session.get('recruiter_id')
        
        # Min size is now always 1, Max is specified by user
        min_size = 1
        max_size = request.form.get('team_size_max')
        team_size_str = f"Max {max_size} Members" if max_size else request.form.get('team_size')

        data = {
            'title': request.form.get('title'),
            'description': request.form.get('description'),
            'theme': request.form.get('theme'),
            'start_date': request.form.get('start_date'),
            'end_date': request.form.get('end_date'),
            'venue': request.form.get('venue'),
            'mode': request.form.get('mode'),
            'team_size': team_size_str,
            'team_size_min': min_size,
            'team_size_max': max_size,
            'prize_details': request.form.get('prize_details'),
            'registration_deadline': request.form.get('registration_deadline')
        }

        # Validation
        required_fields = ['title', 'description', 'theme', 'start_date', 'end_date', 'venue', 'mode', 'team_size_max', 'prize_details', 'registration_deadline']
        if any(not data.get(k) for k in required_fields):
            flash('All fields marked with * are required.', 'danger')
            return render_template('recruiter/hackathon_form.html')
        
        try:
            hackathon_id = recruiter_post_service.create_hackathon(recruiter_id, data)
            if hackathon_id:
                flash('Hackathon created successfully!', 'success')
                return redirect(url_for('recruiter.dashboard'))
            else:
                flash('Failed to create hackathon.', 'danger')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')

    return render_template('recruiter/hackathon_form.html')
