"""
Profile forms using Flask-WTF.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SubmitField, URLField
from wtforms.validators import Optional, URL, Length


class EditProfileForm(FlaskForm):
    """Form for editing user profile information."""
    
    bio = TextAreaField('Bio', validators=[
        Optional(),
        Length(max=1000, message="Bio must be less than 1000 characters.")
    ])
    
    education = StringField('Education', validators=[
        Optional(),
        Length(max=255, message="Education must be less than 255 characters.")
    ])
    
    skills = StringField('Skills (comma separated)', validators=[
        Optional(),
        Length(max=500, message="Skills must be less than 500 characters.")
    ])
    
    github_link = URLField('GitHub Profile URL', validators=[
        Optional(),
        URL(message="Please enter a valid URL.")
    ])
    
    linkedin_link = URLField('LinkedIn Profile URL', validators=[
        Optional(),
        URL(message="Please enter a valid URL.")
    ])
    
    profile_pic = FileField('Profile Picture', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Only JPG and PNG images are allowed.')
    ])
    
    resume = FileField('Resume (PDF)', validators=[
        Optional(),
        FileAllowed(['pdf'], 'Only PDF files are allowed.')
    ])
    
    submit = SubmitField('Save Changes')
