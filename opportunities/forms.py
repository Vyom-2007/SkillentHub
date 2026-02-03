"""
Opportunities forms for job applications.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField


class ApplicationForm(FlaskForm):
    """Form for submitting a job application with resume."""
    
    resume = FileField(
        'Resume (PDF only)',
        validators=[
            FileRequired(message='Please upload your resume.'),
            FileAllowed(['pdf'], message='Only PDF files are allowed.')
        ]
    )
    
    submit = SubmitField('Submit Application')
