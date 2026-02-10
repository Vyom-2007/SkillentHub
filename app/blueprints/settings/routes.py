from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from database.connection import get_db_connection

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

@settings_bp.route('/', methods=['GET', 'POST'])
def index():
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        # Handle password change or other settings
        pass
        
    return render_template('settings/index.html')
    
@settings_bp.route('/change-password', methods=['POST'])
def change_password():
    # Implement password change logic here
    flash('Password change feature coming soon.', 'info')
    return redirect(url_for('settings.index'))
