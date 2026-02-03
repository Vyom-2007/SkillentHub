"""
Admin panel forms for managing jobs and events.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.fields import DateTimeLocalField
from wtforms.validators import DataRequired, Length, Optional


class JobForm(FlaskForm):
    """Form for adding/editing job opportunities."""
    
    title = StringField(
        'Job Title',
        validators=[
            DataRequired(message='Job title is required.'),
            Length(min=3, max=200, message='Title must be between 3 and 200 characters.')
        ]
    )
    
    company = StringField(
        'Company Name',
        validators=[
            DataRequired(message='Company name is required.'),
            Length(min=2, max=200, message='Company name must be between 2 and 200 characters.')
        ]
    )
    
    job_type = SelectField(
        'Job Type',
        choices=[
            ('Full-time', 'Full-time'),
            ('Part-time', 'Part-time'),
            ('Internship', 'Internship'),
            ('Remote', 'Remote'),
            ('Contract', 'Contract')
        ],
        validators=[DataRequired()]
    )
    
    location = StringField(
        'Location',
        validators=[
            Optional(),
            Length(max=200, message='Location must be at most 200 characters.')
        ]
    )
    
    salary_range = StringField(
        'Salary Range',
        validators=[
            Optional(),
            Length(max=100, message='Salary range must be at most 100 characters.')
        ]
    )
    
    description = TextAreaField(
        'Job Description',
        validators=[
            DataRequired(message='Description is required.'),
            Length(min=20, max=5000, message='Description must be between 20 and 5000 characters.')
        ]
    )
    
    requirements = TextAreaField(
        'Requirements',
        validators=[
            Optional(),
            Length(max=3000, message='Requirements must be at most 3000 characters.')
        ]
    )
    
    submit = SubmitField('Post Job')


class EventForm(FlaskForm):
    """Form for adding/editing events."""
    
    title = StringField(
        'Event Title',
        validators=[
            DataRequired(message='Event title is required.'),
            Length(min=3, max=200, message='Title must be between 3 and 200 characters.')
        ]
    )
    
    event_type = SelectField(
        'Event Type',
        choices=[
            ('event', 'General Event'),
            ('competition', 'Competition'),
            ('hackathon', 'Hackathon'),
            ('workshop', 'Workshop'),
            ('webinar', 'Webinar'),
            ('meetup', 'Meetup')
        ],
        validators=[DataRequired()]
    )
    
    event_date = DateTimeLocalField(
        'Event Date & Time',
        format='%Y-%m-%dT%H:%M',
        validators=[DataRequired(message='Event date is required.')]
    )
    
    location = StringField(
        'Location',
        validators=[
            Optional(),
            Length(max=200, message='Location must be at most 200 characters.')
        ]
    )
    
    max_participants = StringField(
        'Max Participants (leave empty for unlimited)',
        validators=[Optional()]
    )
    
    description = TextAreaField(
        'Event Description',
        validators=[
            DataRequired(message='Description is required.'),
            Length(min=20, max=5000, message='Description must be between 20 and 5000 characters.')
        ]
    )
    
    submit = SubmitField('Create Event')
