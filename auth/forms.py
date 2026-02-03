"""
Authentication forms using Flask-WTF.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError


class SignupForm(FlaskForm):
    """Form for user registration."""
    
    full_name = StringField('Full Name', validators=[
        DataRequired(message="Full name is required."),
        Length(min=2, max=100, message="Full name must be between 2 and 100 characters.")
    ])
    
    email = StringField('Email', validators=[
        DataRequired(message="Email is required."),
        Email(message="Please enter a valid email address.")
    ])
    
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required."),
        Length(min=6, message="Password must be at least 6 characters long.")
    ])
    
    confirm = PasswordField('Confirm Password', validators=[
        DataRequired(message="Please confirm your password."),
        EqualTo('password', message="Passwords must match.")
    ])
    
    submit = SubmitField('Sign Up')


class LoginForm(FlaskForm):
    """Form for user login."""
    
    email = StringField('Email', validators=[
        DataRequired(message="Email is required."),
        Email(message="Please enter a valid email address.")
    ])
    
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required.")
    ])
    
    submit = SubmitField('Login')


class ForgotPasswordForm(FlaskForm):
    """Form for requesting password reset OTP."""
    
    email = StringField('Email', validators=[
        DataRequired(message="Email is required."),
        Email(message="Please enter a valid email address.")
    ])
    
    submit = SubmitField('Send OTP')


class ResetPasswordForm(FlaskForm):
    """Form for resetting password with OTP."""
    
    otp = StringField('OTP Code', validators=[
        DataRequired(message="OTP code is required."),
        Length(min=6, max=6, message="OTP must be exactly 6 digits.")
    ])
    
    new_password = PasswordField('New Password', validators=[
        DataRequired(message="New password is required."),
        Length(min=6, message="Password must be at least 6 characters long.")
    ])
    
    submit = SubmitField('Reset Password')
