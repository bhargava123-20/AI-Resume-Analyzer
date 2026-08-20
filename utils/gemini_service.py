"""
Forwarding module to utils.gemini_service for backward compatibility.
"""

from utils.gemini_service import (
    get_gemini_api_key,
    is_gemini_configured,
    generate_ai_resume_feedback,
    generate_ai_resume_feedback as generate_ai_resume_analysis,
    generate_cover_letter
)
