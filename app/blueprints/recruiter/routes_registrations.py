"""
Recruiter Event Registrations Routes.
View registrations and Export CSV.
"""
from flask import render_template, Response, flash, redirect, url_for, session
from app.blueprints.recruiter.routes import recruiter_bp
from app.utils.decorators import recruiter_required
from app.services import recruiter_export_service
from datetime import datetime

@recruiter_bp.route('/<item_type>/<int:item_id>/registrations')
@recruiter_required
def view_registrations(item_type, item_id):
    recruiter_id = session.get('recruiter_id')
    
    if item_type not in ['competition', 'hackathon']:
        flash('Invalid event type', 'danger')
        return redirect(url_for('recruiter.manage_opportunities'))
        
    data = recruiter_export_service.get_event_registrations(item_type, item_id, recruiter_id)
    
    if not data:
        flash('Event not found or access denied', 'danger')
        return redirect(url_for('recruiter.manage_opportunities'))
        
    return render_template('recruiter/registrations_list.html', 
                           registrations=data['registrations'],
                           event_title=data['event_title'],
                           item_type=item_type,
                           item_id=item_id)

@recruiter_bp.route('/<item_type>/<int:item_id>/registrations/export')
@recruiter_required
def export_registrations(item_type, item_id):
    recruiter_id = session.get('recruiter_id')
    
    if item_type not in ['competition', 'hackathon']:
        flash('Invalid event type', 'danger')
        return redirect(url_for('recruiter.manage_opportunities'))
        
    data = recruiter_export_service.get_event_registrations(item_type, item_id, recruiter_id)
    
    if not data:
        flash('Event not found or access denied', 'danger')
        return redirect(url_for('recruiter.manage_opportunities'))
        
    csv_content = recruiter_export_service.generate_registrations_csv(
        data['registrations'], data['event_title']
    )
    
    filename = f"registrations_{item_type}_{item_id}_{datetime.now().strftime('%Y%m%d')}.csv"
    
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )
