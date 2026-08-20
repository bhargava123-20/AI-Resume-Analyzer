"""
Forwarding module to utils.analyzer for backward compatibility.
"""

 
    analyze_strengths_and_weaknesses,
    analyze_ats_compatibility,
    generate_improvement_suggestions,
    ACTION_VERBS

from utils.matching import (
    calculate_tfidf_similarity,
    calculate_resume_job_match,
    extract_jd_requirements
)
from utils.gemini_service import (
    generate_ai_resume_feedback,
    generate_ai_resume_feedback as generate_ai_resume_analysis,
    generate_cover_letter,
    is_gemini_configured
)
