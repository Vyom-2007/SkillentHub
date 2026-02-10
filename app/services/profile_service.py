from app.models.profile import Profile, Education, Skills
import os
from flask import current_app
from werkzeug.utils import secure_filename

class ProfileService:
    @staticmethod
    def get_full_profile(user_id):
        profile = Profile.get_by_user_id(user_id)
        education = Education.get_by_user_id(user_id)
        skills = Skills.get_user_skills(user_id)
        return {
            "profile": profile,
            "education": education,
            "skills": skills
        }

    @staticmethod
    def update_profile(user_id, form_data, files):
        # Handle file upload
        profile_pic_path = form_data.get('existing_profile_picture')
        resume_path = form_data.get('existing_resume_path')
        
        if 'profile_picture' in files:
            file = files['profile_picture']
            if file and file.filename:
                filename = secure_filename(f"user_{user_id}_{file.filename}")
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], 'profiles', filename))
                profile_pic_path = f"profiles/{filename}"
                
        if 'resume' in files:
            file = files['resume']
            if file and file.filename:
                filename = secure_filename(f"resume_{user_id}_{file.filename}")
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], 'resumes', filename))
                resume_path = f"resumes/{filename}"
        
        data = {
            'headline': form_data.get('headline'),
            'bio': form_data.get('bio'),
            'location': form_data.get('location'),
            'phone': form_data.get('phone'),
            'profile_picture': profile_pic_path,
            'resume_path': resume_path,
            'profile_completion': ProfileService._calculate_completion(form_data, profile_pic_path)
        }
        
        return Profile.create_or_update(user_id, data)

    @staticmethod
    def _calculate_completion(data, pic_path):
        score = 0
        if data.get('headline'): score += 20
        if data.get('bio'): score += 20
        if data.get('location'): score += 10
        if pic_path: score += 20
        # Check specific tables for other scores if needed, simplifying here
        return min(score + 30, 100) # Base 30 for registering

    @staticmethod
    def add_education(user_id, form_data):
        return Education.add(user_id, form_data)
        
    @staticmethod
    def delete_education(user_id, education_id):
        return Education.delete(education_id, user_id)
        
    @staticmethod
    def get_all_available_skills():
        return Skills.get_all_skills()
        
    @staticmethod
    def add_skill(user_id, skill_id, proficiency):
        return Skills.add_user_skill(user_id, skill_id, proficiency)
        
    @staticmethod
    def remove_skill(user_id, skill_id):
        return Skills.remove_user_skill(user_id, skill_id)
