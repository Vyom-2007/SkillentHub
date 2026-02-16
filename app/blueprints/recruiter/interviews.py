from flask import render_template, request, redirect, url_for, flash, session, jsonify
from app.blueprints.recruiter.routes import recruiter_bp
from app.utils.decorators import recruiter_required
from app.services import interview_service, recruiter_manage_service

@recruiter_bp.route('/interviews')
@recruiter_required
def list_interviews():
    """List all scheduled interviews for the recruiter."""
    recruiter_id = session.get('recruiter_id')
    interviews = interview_service.get_interviews_for_recruiter(recruiter_id)
    return render_template('recruiter/interviews/list.html', interviews=interviews)

@recruiter_bp.route('/applications/<int:application_id>/schedule', methods=['POST'])
@recruiter_required
def schedule_interview(application_id):
    """Schedule an interview for an application."""
    recruiter_id = session.get('recruiter_id')
    
    # Verify application belongs to recruiter
    app_details = recruiter_manage_service.get_application_detail(application_id, recruiter_id)
    if not app_details:
        flash('Application not found or access denied', 'danger')
        return redirect(url_for('recruiter.applications'))

    scheduled_at = request.form.get('scheduled_at')
    mode = request.form.get('mode')
    location_url = request.form.get('location_url')
    notes = request.form.get('notes')
    
    if not scheduled_at or not mode:
        flash('Date/Time and Mode are required', 'warning')
        return redirect(url_for('recruiter.application_detail', application_id=application_id))

    try:
        interview_id = interview_service.schedule_interview(
            application_id=application_id,
            recruiter_id=recruiter_id,
            candidate_id=app_details['user_id'],
            scheduled_at=scheduled_at,
            mode=mode,
            location_url=location_url,
            notes=notes
        )
        
        if interview_id:
            flash('Interview scheduled successfully', 'success')
            # Also update application status to 'Interview' if not already?
            # Keeping it separate allows flexibility, but usually scheduling implies 'Interview' status.
            recruiter_manage_service.update_application_status(application_id, 'interview', recruiter_id)
        else:
            flash('Failed to schedule interview', 'danger')
            
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')

    return redirect(url_for('recruiter.application_detail', application_id=application_id))

@recruiter_bp.route('/interviews/<int:interview_id>/update-status', methods=['POST'])
@recruiter_required
def update_interview_status(interview_id):
    """Update interview status (Complete/Cancel)."""
    recruiter_id = session.get('recruiter_id')
    new_status = request.form.get('status')
    
    if new_status not in ['completed', 'cancelled']:
         flash('Invalid status update', 'warning')
         return redirect(url_for('recruiter.list_interviews'))

    success, msg = interview_service.update_interview_status(interview_id, new_status, 'recruiter', recruiter_id)
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')
        
    return redirect(request.referrer or url_for('recruiter.list_interviews'))
