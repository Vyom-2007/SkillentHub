import os
import secrets
from PIL import Image
from flask import current_app
from werkzeug.utils import secure_filename

def save_profile_picture(form_picture, user_id):
    # Rename: {user_id}_{hex}.{ext}
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = f"{user_id}_{random_hex}{f_ext}"
    picture_path = os.path.join(current_app.root_path, '..', 'uploads', 'profiles', picture_fn)
    
    # Resize/Crop
    output_size = (300, 300)
    i = Image.open(form_picture)
    
    # simple resize to square-ish? Or crop center?
    # Pillow ImageOps.fit is good for cropping
    from PIL import ImageOps
    i = ImageOps.fit(i, output_size, Image.Resampling.LANCZOS)
    
    i.save(picture_path)
    
    return picture_fn

def save_resume(form_file, user_id):
    random_hex = secrets.token_hex(8)
    # Ensure PDF
    if not form_file.filename.lower().endswith('.pdf'):
        return None
        
    filename = secure_filename(form_file.filename)
    file_fn = f"{user_id}_{random_hex}_{filename}"
    file_path = os.path.join(current_app.root_path, '..', 'uploads', 'resumes', file_fn)
    
    form_file.save(file_path)
    return file_fn

def save_post_image(form_picture, user_id):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = f"{user_id}_{random_hex}{f_ext}"
    picture_path = os.path.join(current_app.root_path, '..', 'uploads', 'posts', picture_fn)
    
    i = Image.open(form_picture)
    # Limit max size but allow aspect ratio
    i.thumbnail((1024, 1024))
    i.save(picture_path)
    
    return picture_fn
