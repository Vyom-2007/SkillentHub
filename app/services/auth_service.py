from app.models.user import User
from flask import session

class AuthService:
    @staticmethod
    def register_user(email, password, full_name):
        if User.get_by_email(email):
            return {"error": "Email already exists"}
            
        user_id = User.create(email, password, full_name)
        if user_id:
            return {"success": True, "user_id": user_id}
        return {"error": "Registration failed"}

    @staticmethod
    def login_user(email, password):
        user = User.get_by_email(email)
        if user and User.verify_password(user['password_hash'], password):
            session['user_id'] = user['user_id']
            session['full_name'] = user['full_name']
            session.permanent = True
            return {"success": True, "user": user}
        return {"error": "Invalid email or password"}

    @staticmethod
    def logout_user():
        session.clear()
        return {"success": True}
        
    @staticmethod
    def get_current_user():
        if 'user_id' in session:
            return User.get_by_id(session['user_id'])
        return None
