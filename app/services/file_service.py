import os
import uuid
from PIL import Image
from flask import current_app


ALLOWED_IMAGE_EXT = {'jpg', 'jpeg', 'png'}
ALLOWED_DOC_EXT = {'pdf', 'docx'}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB


def allowed_image(filename):
    """Check if the file extension is an allowed image type."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXT


def allowed_document(filename):
    """Check if the file extension is an allowed document type."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_DOC_EXT


def _ensure_dir(directory):
    """Create directory if it doesn't exist."""
    os.makedirs(directory, exist_ok=True)


def save_profile_picture(file, user_id):
    """
    Validate image (JPG/PNG) via Pillow, resize to 400×400 max,
    save to uploads/profiles/.  Returns the relative path from project root.
    """
    if not file or not file.filename:
        return None

    if not allowed_image(file.filename):
        raise ValueError('Only JPG and PNG images are allowed.')

    # Read into memory to check size
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)

    if size > MAX_IMAGE_SIZE:
        raise ValueError('Image must be under 5 MB.')

    # Validate & resize with Pillow
    try:
        img = Image.open(file)
        img.verify()          # Check it's a real image
        file.seek(0)          # Reset after verify
        img = Image.open(file)  # Re-open for processing
    except Exception:
        raise ValueError('Invalid image file.')

    # Convert to RGB if necessary (e.g. RGBA PNGs)
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')

    # Resize preserving aspect ratio, then center-crop to 400×400
    img.thumbnail((400, 400), Image.LANCZOS)

    # Generate unique filename
    ext = 'jpg'
    filename = f"user_{user_id}_{uuid.uuid4().hex[:8]}.{ext}"
    upload_dir = os.path.join(current_app.root_path, '..', 'uploads', 'profiles')
    _ensure_dir(upload_dir)

    filepath = os.path.join(upload_dir, filename)
    img.save(filepath, 'JPEG', quality=90)

    return f"uploads/profiles/{filename}"


def save_document(file, user_id, doc_type='resume'):
    """
    Validate PDF/DOCX, save to uploads/resumes/.
    doc_type: 'resume' or 'cover_letter'
    Returns the relative path from project root.
    """
    if not file or not file.filename:
        return None

    if not allowed_document(file.filename):
        raise ValueError('Only PDF and DOCX files are allowed.')

    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{doc_type}_{user_id}_{uuid.uuid4().hex[:8]}.{ext}"
    upload_dir = os.path.join(current_app.root_path, '..', 'uploads', 'resumes')
    _ensure_dir(upload_dir)

    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)

    return f"uploads/resumes/{filename}"
