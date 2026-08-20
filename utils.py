"""
Helper utilities re-exporting resume_parser, matching, analyzer, and gemini_service.
"""

from utils.resume_parser import (
    validate_and_extract_pdf,
    extract_text_from_pdf,
    clean_text,
    extract_structured_resume
)
from utils.matching import (
    calculate_tfidf_similarity,
    extract_jd_requirements,
    calculate_resume_job_match
)
from utils.analyzer import (
    analyze_strengths_and_weaknesses,
    analyze_ats_compatibility,
    generate_improvement_suggestions
)
from utils.gemini_service import (
    get_gemini_api_key,
    is_gemini_configured,
    generate_ai_resume_analysis,
    generate_cover_letter
)
