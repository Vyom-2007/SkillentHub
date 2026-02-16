import re
import os
import logging

def extract_text_from_pdf(file_path):
    text = ""
    try:
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    except Exception as e:
        logging.error(f"Error extracting PDF: {e}")
    return text

def extract_text_from_docx(file_path):
    text = ""
    try:
        import docx
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        logging.error(f"Error extracting DOCX: {e}")
    return text

def extract_text_from_txt(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception:
        return ""

def clean_text(text):
    # Remove excessive whitespace
    return re.sub(r'\s+', ' ', text).strip()

def parse_resume(file_path):
    """
    Parse a resume file and extract structured data.
    Returns:
        dict: {'skills': [str], 'education': [{'degree': str, 'institution': str}], 'experience': [{'title': str, 'company': str}]}
    """
    ext = os.path.splitext(file_path)[1].lower()
    text = ""
    
    if ext == '.pdf':
        text = extract_text_from_pdf(file_path)
    elif ext in ['.docx', '.doc']:
        text = extract_text_from_docx(file_path)
    else:
        text = extract_text_from_txt(file_path)
        
    if not text:
        return {'error': 'Could not extract text'}
        
    # Clean text setup
    # text = clean_text(text) # Keep newlines for section detection
    
    data = {
        'skills': [],
        'education': [],
        'experience': []
    }
    
    # --- SKILLS EXTRACTION ---
    # Naive approach: Keyword matching against a common db
    # In a real app, load from DB. Here, hardcoded common tech skills.
    COMMON_SKILLS = {
        'python', 'java', 'c++', 'javascript', 'react', 'node.js', 'flask', 'django', 'sql', 'mysql', 
        'postgresql', 'docker', 'kubernetes', 'aws', 'azure', 'git', 'html', 'css', 'machine learning',
        'data analysis', 'communication', 'leadership', 'teamwork', 'agile', 'scrum', 'project management'
    }
    
    lower_text = text.lower()
    found_skills = set()
    for skill in COMMON_SKILLS:
        # Simple word boundary check
        if re.search(r'\b' + re.escape(skill) + r'\b', lower_text):
            found_skills.add(skill.capitalize())
            
    data['skills'] = list(found_skills)
    
    # --- SECTIONS ---
    # Identify rough sections
    # Keywords: "Education", "Experience", "Work History", "Skills"
    sections = {
        'education': [],
        'experience': []
    }
    
    lines = text.split('\n')
    current_section = None
    
    education_keywords = ['education', 'academic background', 'qualifications']
    experience_keywords = ['experience', 'work history', 'employment', 'professional background']
    
    for line in lines:
        clean_line = line.strip().lower()
        if not clean_line:
            continue
            
        # Check headers
        is_header = False
        if any(keyword in clean_line for keyword in education_keywords) and len(clean_line) < 30:
            current_section = 'education'
            is_header = True
        elif any(keyword in clean_line for keyword in experience_keywords) and len(clean_line) < 30:
            current_section = 'experience'
            is_header = True
        
        if is_header:
            continue
            
        if current_section == 'education':
            # rudimentary parsing: look for Degree keywords
            # Line example: "B.S. Computer Science, University of X"
            if any(w in clean_line for w in ['b.s', 'bachelor', 'm.s', 'master', 'phd', 'degree', 'university', 'college', 'institute']):
                 # Heuristic: split by comma?
                 # This is very hard to iterate perfectly.
                 # Just append raw line for now if it looks relevant
                 sections['education'].append(line.strip())
                 
        elif current_section == 'experience':
            # look for date patterns or role keywords
            # Line example: "Software Engineer | Google | 2020-Present"
            # Just collect lines that look like headers/content
            sections['experience'].append(line.strip())

    # Format Education
    # Try to structure specifically
    for ed_line in sections['education'][:5]: # Limit to avoid junk
        # Very simple: assume "Degree, School"
         data['education'].append({
             'institution': ed_line, # placeholder logic
             'degree': '',
             'year': ''
         })

    # Format Experience
    # Try to structure
    for exp_line in sections['experience'][:10]:
         data['experience'].append({
             'company': exp_line,
             'position': '',
             'duration': ''
         })

    return data
