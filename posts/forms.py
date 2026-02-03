"""
Post forms using Flask-WTF.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import TextAreaField, SubmitField, URLField
from wtforms.validators import DataRequired, Optional, URL, Length


class PostForm(FlaskForm):
    """Form for creating and editing posts."""
    
    content = TextAreaField('Content', validators=[
        DataRequired(message="Post content is required."),
        Length(min=1, max=2000, message="Content must be between 1 and 2000 characters.")
    ])
    
    image = FileField('Image', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Only JPG and PNG images are allowed.')
    ])
    
    project_link = URLField('Project Link', validators=[
        Optional(),
        URL(message="Please enter a valid URL.")
    ])
    
    submit = SubmitField('Publish Post')
