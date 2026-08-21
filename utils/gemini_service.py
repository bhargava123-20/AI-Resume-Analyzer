"""
Gemini AI service for the AI Resume Analyzer.
"""

import os

try:
    import google.generativeai as genai
except ImportError:
    genai = None


def get_gemini_api_key():
    """Get Gemini API key from environment variables."""
    return os.getenv("GEMINI_API_KEY", "").strip()


def is_gemini_configured():
    """Check whether Gemini API is configured."""
    return bool(get_gemini_api_key()) and genai is not None


def _configure_gemini(api_key=None):
    """Configure Gemini with the supplied or environment API key."""
    key = (api_key or get_gemini_api_key()).strip()

    if not key or genai is None:
        return False

    genai.configure(api_key=key)
    return True


def generate_ai_resume_feedback(
    structured_resume,
    job_desc,
    match_data,
    custom_key=None,
):
    """
    Generate AI resume feedback using Gemini.
    Falls back to local analysis when Gemini is unavailable.
    """

    if not _configure_gemini(custom_key):
        return {
            "notice": "Gemini AI is not configured. Local analysis is being used.",
            "strengths": [],
            "weaknesses": [],
            "missing_skills": match_data.get("missing_skills", []),
            "missing_keywords": match_data.get("missing_keywords", []),
            "suggestions_summary": [],
            "suggestions_projects": [],
            "suggestions_skills_section": [],
            "suggestions_ats": [],
        }

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")

        prompt = f"""
You are an expert resume and ATS analyzer.

Analyze the candidate resume against the target job description.

RESUME:
{structured_resume}

JOB DESCRIPTION:
{job_desc}

MATCH DATA:
{match_data}

Return practical feedback covering:
1. Resume strengths
2. Resume weaknesses
3. Missing skills
4. Missing keywords
5. Professional summary suggestions
6. Project and experience suggestions
7. Skills section suggestions
8. ATS optimization suggestions

Keep the response concise and professional.
"""

        response = model.generate_content(prompt)
        text = response.text if response and response.text else ""

        return {
            "notice": "Gemini AI analysis generated successfully.",
            "strengths": [text],
            "weaknesses": [],
            "missing_skills": match_data.get("missing_skills", []),
            "missing_keywords": match_data.get("missing_keywords", []),
            "suggestions_summary": [],
            "suggestions_projects": [],
            "suggestions_skills_section": [],
            "suggestions_ats": [],
        }

    except Exception as e:
        return {
            "notice": f"Gemini AI unavailable. Local analysis is being used.",
            "strengths": [],
            "weaknesses": [],
            "missing_skills": match_data.get("missing_skills", []),
            "missing_keywords": match_data.get("missing_keywords", []),
            "suggestions_summary": [],
            "suggestions_projects": [],
            "suggestions_skills_section": [],
            "suggestions_ats": [],
        }


def generate_ai_resume_analysis(
    structured_resume,
    job_desc,
    match_data,
    custom_key=None,
):
    """Backward-compatible alias for Gemini resume analysis."""
    return generate_ai_resume_feedback(
        structured_resume,
        job_desc,
        match_data,
        custom_key=custom_key,
    )


def generate_cover_letter(
    structured_resume,
    job_desc,
    company_name="Hiring Team",
    target_role="Target Role",
    custom_key=None,
):
    """Generate a professional cover letter."""

    if not _configure_gemini(custom_key):
        candidate_name = structured_resume.get("name", "Candidate")

        return f"""Dear Hiring Team,

I am writing to express my interest in the {target_role} position at {company_name}.

My background, technical skills, projects, and experience make me enthusiastic about contributing to your organization.

I would welcome the opportunity to discuss how my skills and experience can contribute to your team.

Thank you for your time and consideration.

Sincerely,
{candidate_name}
"""

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")

        prompt = f"""
Write a professional, personalized cover letter.

Candidate Resume:
{structured_resume}

Job Description:
{job_desc}

Company:
{company_name}

Target Role:
{target_role}

Use information from the resume and job description.
Do not invent qualifications.
Keep the cover letter professional and concise.
"""

        response = model.generate_content(prompt)

        if response and response.text:
            return response.text

    except Exception:
        pass

    candidate_name = structured_resume.get("name", "Candidate")

    return f"""Dear Hiring Team,

I am writing to express my interest in the {target_role} position at {company_name}.

I believe my technical skills, projects, and experience align well with the requirements of this role.

Thank you for considering my application.

Sincerely,
{candidate_name}
"""
