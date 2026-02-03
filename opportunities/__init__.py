"""
Opportunities module initialization.

This module handles job opportunities listing and applications.
"""

from opportunities.routes import opportunities_bp
from opportunities.forms import ApplicationForm

__all__ = ['opportunities_bp', 'ApplicationForm']
