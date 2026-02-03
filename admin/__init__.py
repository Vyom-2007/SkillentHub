"""
Admin module initialization.

This module handles the admin panel for managing jobs, events, and users.
"""

from admin.routes import admin_bp
from admin.forms import JobForm, EventForm

__all__ = ['admin_bp', 'JobForm', 'EventForm']
