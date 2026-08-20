"""
Forwarding parser module to resume_parser to ensure backward compatibility.
"""

from resume_parser import (
    validate_and_extract_pdf,
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_from_txt,
    parse_uploaded_file,
    clean_text,
    extract_structured_resume,
    extract_resume,
    extract_keywords_and_skills,
    extract_name,
    extract_email,
    extract_phone,
    extract_sections
)
