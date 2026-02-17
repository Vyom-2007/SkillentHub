"""
Recruiter Management Routes.
Handles 'My Opportunities' and 'ATS' (Applications).
"""
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from app.blueprints.recruiter.routes import recruiter_bp
from app.utils.decorators import recruiter_required
from app.services import recruiter_manage_service

# --- OPPORTUNITIES MANAGEMENT ---

@recruiter_bp.route('/opportunities')
@recruiter_required
def manage_opportunities():
    recruiter_id = session.get('recruiter_id')
    status_filter = request.args.get('status')
    search_query = request.args.get('search')
    
    opportunities = recruiter_manage_service.get_posted_opportunities(
        recruiter_id, status_filter, search_query
    )
    
    return render_template('recruiter/manage_opportunities.html', 
                           opportunities=opportunities,
                           filter_status=status_filter)

@recruiter_bp.route('/opportunities/<item_type>/<int:item_id>/toggle', methods=['POST'])
@recruiter_required
def toggle_opportunity(item_type, item_id):
    recruiter_id = session.get('recruiter_id')
    success = recruiter_manage_service.toggle_opportunity_status(item_type, item_id, recruiter_id)
    
    if success:
        return jsonify({'success': True, 'message': 'Status updated'})
    else:
        return jsonify({'success': False, 'message': 'Failed to update status'}), 400

# --- ATS (APPLICATIONS) ---

@recruiter_bp.route('/applications')
@recruiter_required
def applications():
    recruiter_id = session.get('recruiter_id')
    
    filters = {
        'status': request.args.get('status'),
        'item_type': request.args.get('item_type')
    }
    
    apps = recruiter_manage_service.get_applications(recruiter_id, filters)
    
    return render_template('recruiter/applications_list.html', 
                           applications=apps, 
                           filters=filters)

@recruiter_bp.route('/applications/<int:application_id>')
@recruiter_required
def application_detail(application_id):
    recruiter_id = session.get('recruiter_id')
    
    app_details = recruiter_manage_service.get_application_detail(application_id, recruiter_id)
    
    if not app_details:
        flash('Application not found or access denied', 'danger')
        return redirect(url_for('recruiter.applications'))
    
    notes = recruiter_manage_service.get_notes(application_id)
    history = recruiter_manage_service.get_application_history(application_id)
    
    from app.services.application_service import ALLOWED_TRANSITIONS
    
    return render_template('recruiter/application_detail.html', 
                           app=app_details, 
                           notes=notes,
                           history=history,
                           allowed_transitions=ALLOWED_TRANSITIONS)

@recruiter_bp.route('/applications/<int:application_id>/status', methods=['POST'])
@recruiter_required
def update_application_status(application_id):
    recruiter_id = session.get('recruiter_id')
    new_status = request.form.get('status')
    
    success, message = recruiter_manage_service.update_application_status(application_id, new_status, recruiter_id)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
        
    next_url = request.args.get('next') or request.form.get('next')
    if next_url:
        return redirect(next_url)
        
    return redirect(url_for('recruiter.application_detail', application_id=application_id))

@recruiter_bp.route('/applications/<int:application_id>/note', methods=['POST'])
@recruiter_required
def add_application_note(application_id):
    recruiter_id = session.get('recruiter_id')
    content = request.form.get('content')
    
    if content:
        success = recruiter_manage_service.add_note(application_id, recruiter_id, content)
        if success:
            flash('Note added', 'success')
        else:
            flash('Failed to add note. Unauthorized or valid application not found.', 'danger')
    
    return redirect(url_for('recruiter.application_detail', application_id=application_id))
