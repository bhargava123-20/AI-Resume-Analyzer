"""
Resume analysis utilities for the AI Resume Analyzer.
"""

import re


# Common strong action verbs for resume analysis
ACTION_VERBS = {
    "achieved",
    "analyzed",
    "built",
    "created",
    "designed",
    "developed",
    "implemented",
    "improved",
    "increased",
    "integrated",
    "led",
    "managed",
    "optimized",
    "organized",
    "reduced",
    "resolved",
    "tested",
    "trained",
    "automated",
}


def analyze_strengths_and_weaknesses(structured_resume, match_data):
    """
    Analyze resume strengths and weaknesses based on extracted
    resume information and job matching results.
    """

    structured_resume = structured_resume or {}
    match_data = match_data or {}

    strengths = []
    weaknesses = []

    technical_skills = structured_resume.get("technical_skills", []) or []
    programming_languages = structured_resume.get(
        "programming_languages", []
    ) or []
    tools_and_tech = structured_resume.get("tools_and_tech", []) or []
    education = structured_resume.get("education", []) or []
    certifications = structured_resume.get("certifications", []) or []
    projects = structured_resume.get("projects", []) or []
    experience = structured_resume.get("experience", []) or []

    matched_skills = match_data.get("matched_skills", []) or []
    missing_skills = match_data.get("missing_skills", []) or []

    skills_score = match_data.get("skills_score", 0)
    overall_score = match_data.get("overall_score", 0)

    total_technical_items = (
        len(technical_skills)
        + len(programming_languages)
        + len(tools_and_tech)
    )

    # Strengths
    if total_technical_items >= 5:
        strengths.append(
            "Strong technical skills and technology coverage."
        )
    elif total_technical_items > 0:
        strengths.append(
            "Technical skills are present and clearly identifiable."
        )

    if matched_skills:
        strengths.append(
            f"Good alignment with the target role: "
            f"{len(matched_skills)} required skills matched."
        )

    if skills_score >= 75:
        strengths.append(
            "The resume has a strong skills match with the job description."
        )

    if projects:
        strengths.append(
            f"Projects are included, providing practical experience "
            f"evidence ({len(projects)} project(s) detected)."
        )

    if experience:
        strengths.append(
            "Work experience or professional experience is present."
        )

    if certifications:
        strengths.append(
            f"Relevant certifications are listed ({len(certifications)} detected)."
        )

    if education:
        strengths.append(
            "Educational background is available."
        )

    if overall_score >= 75:
        strengths.append(
            "Overall resume-to-job alignment is strong."
        )

    # Weaknesses
    if missing_skills:
        weaknesses.append(
            f"{len(missing_skills)} required skill(s) from the job description "
            "are missing or not clearly demonstrated."
        )

    if skills_score < 55:
        weaknesses.append(
            "The technical skills match with the target job could be improved."
        )

    if not projects:
        weaknesses.append(
            "No projects were clearly detected. Adding relevant projects "
            "could strengthen the resume."
        )

    if not experience:
        weaknesses.append(
            "No work experience was clearly detected. Relevant internships, "
            "training, or practical experience can be highlighted."
        )

    if not certifications:
        weaknesses.append(
            "No certifications were clearly detected."
        )

    if not education:
        weaknesses.append(
            "Education details were not clearly detected."
        )

    if not strengths:
        strengths.append(
            "The resume contains basic information that can be further optimized."
        )

    if not weaknesses:
        weaknesses.append(
            "No major weaknesses were detected from the available information."
        )

    return {
        "strengths": strengths,
        "weaknesses": weaknesses,
    }


def analyze_ats_compatibility(structured_resume, job_desc):
    """
    Perform a simple ATS compatibility analysis.
    """

    structured_resume = structured_resume or {}
    job_desc = job_desc or ""

    resume_parts = []

    for key in [
        "name",
        "email",
        "phone",
        "summary",
    ]:
        value = structured_resume.get(key)
        if value:
            resume_parts.append(str(value))

    for key in [
        "technical_skills",
        "programming_languages",
        "tools_and_tech",
        "soft_skills",
        "education",
        "certifications",
        "projects",
        "experience",
    ]:
        value = structured_resume.get(key, [])
        if isinstance(value, list):
            resume_parts.extend(str(item) for item in value)
        elif value:
            resume_parts.append(str(value))

    resume_text = " ".join(resume_parts).lower()
    job_text = str(job_desc).lower()

    if not resume_text or not job_text:
        return {
            "ats_score": 0,
            "matched_keywords": [],
            "missing_keywords": [],
            "recommendations": [
                "Provide both resume information and a job description."
            ],
        }

    # Extract meaningful words from job description
    job_words = re.findall(r"\b[a-zA-Z][a-zA-Z0-9+#.\-]{2,}\b", job_text)

    stop_words = {
        "the",
        "and",
        "for",
        "with",
        "that",
        "this",
        "from",
        "are",
        "you",
        "your",
        "our",
        "will",
        "have",
        "has",
        "job",
        "role",
        "work",
        "years",
        "using",
        "into",
        "their",
        "they",
        "about",
        "required",
        "requirements",
        "responsibilities",
        "experience",
        "skills",
    }

    keywords = []

    for word in job_words:
        normalized = word.lower().strip(".,;:()[]{}")
        if normalized not in stop_words and len(normalized) >= 3:
            if normalized not in keywords:
                keywords.append(normalized)

    matched_keywords = [
        keyword for keyword in keywords
        if keyword in resume_text
    ]

    missing_keywords = [
        keyword for keyword in keywords
        if keyword not in resume_text
    ]

    if keywords:
        ats_score = round(
            (len(matched_keywords) / len(keywords)) * 100,
            2,
        )
    else:
        ats_score = 0

    recommendations = []

    if missing_keywords:
        recommendations.append(
            "Add relevant missing job-description keywords naturally "
            "where they accurately describe your experience."
        )

    if len(resume_text.split()) < 150:
        recommendations.append(
            "Consider adding more relevant detail to the resume."
        )

    if not structured_resume.get("projects"):
        recommendations.append(
            "Add relevant projects with technologies and measurable outcomes."
        )

    if not structured_resume.get("certifications"):
        recommendations.append(
            "Add relevant certifications if available."
        )

    if not recommendations:
        recommendations.append(
            "Resume keyword coverage looks good. Continue using clear "
            "ATS-friendly headings and measurable achievements."
        )

    return {
        "ats_score": ats_score,
        "matched_keywords": matched_keywords[:50],
        "missing_keywords": missing_keywords[:50],
        "recommendations": recommendations,
    }


def generate_improvement_suggestions(
    structured_resume,
    match_data,
    job_desc,
):
    """
    Generate practical resume improvement suggestions.
    """

    structured_resume = structured_resume or {}
    match_data = match_data or {}
    job_desc = job_desc or ""

    suggestions = []

    missing_skills = match_data.get("missing_skills", []) or []
    missing_keywords = match_data.get("missing_keywords", []) or []
    overall_score = match_data.get("overall_score", 0)
    skills_score = match_data.get("skills_score", 0)

    if missing_skills:
        suggestions.append(
            "Add relevant missing skills from the job description only "
            "if you genuinely have those skills."
        )

    if missing_keywords:
        suggestions.append(
            "Review the job description and naturally include important "
            "matching keywords in the appropriate resume sections."
        )

    if overall_score < 55:
        suggestions.append(
            "Improve alignment between the resume and target job by "
            "highlighting the most relevant skills and experience."
        )
    elif overall_score < 75:
        suggestions.append(
            "Strengthen the resume's job alignment by adding more "
            "role-specific achievements and keywords."
        )
    else:
        suggestions.append(
            "Maintain the strong job alignment and focus on measurable "
            "achievements."
        )

    if skills_score < 60:
        suggestions.append(
            "Improve the skills section by grouping technical skills, "
            "programming languages, frameworks, and tools clearly."
        )

    if not structured_resume.get("projects"):
        suggestions.append(
            "Add 2–3 relevant projects with technologies used, your role, "
            "and measurable results."
        )

    if not structured_resume.get("experience"):
        suggestions.append(
            "Highlight internships, academic projects, training, or "
            "practical experience relevant to the target role."
        )

    if not structured_resume.get("certifications"):
        suggestions.append(
            "Add relevant certifications or courses if you have completed them."
        )

    suggestions.append(
        "Use strong action verbs such as developed, implemented, designed, "
        "optimized, automated, and analyzed when describing achievements."
    )

    suggestions.append(
        "Whenever possible, quantify achievements using percentages, "
        "numbers, time saved, users served, or other measurable results."
    )

    suggestions.append(
        "Keep formatting simple and consistent so ATS systems can easily "
        "read the resume."
    )

    # Remove duplicates while preserving order
    unique_suggestions = []
    seen = set()

    for suggestion in suggestions:
        if suggestion not in seen:
            unique_suggestions.append(suggestion)
            seen.add(suggestion)

    return unique_suggestions
