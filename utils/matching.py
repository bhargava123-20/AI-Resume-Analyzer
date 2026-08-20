"""
Resume-Job Description Matching Engine
Uses scikit-learn TF-IDF cosine similarity, NLP skill extraction,
and domain weighting to calculate match scores and skill/keyword gaps.
"""

import re
from typing import Dict, List, Set, Tuple, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .resume_parser import (
    PROGRAMMING_LANGUAGES,
    TOOLS_AND_TECHNOLOGIES,
    SOFT_SKILLS,
    extract_keywords,
    clean_text
)


def calculate_tfidf_similarity(text1: str, text2: str) -> float:
    """
    Calculates TF-IDF Cosine Similarity between two text documents (0.0 to 1.0).
    """
    if not text1.strip() or not text2.strip():
        return 0.0
    try:
        vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return float(similarity)
    except Exception:
        return 0.0


def extract_jd_requirements(job_desc: str) -> Dict[str, Any]:
    """
    Analyzes job description to extract required/preferred skills, technologies,
    qualifications, experience requirements, and key terms.
    """
    jd_clean = clean_text(job_desc)
    jd_lower = jd_clean.lower()

    # Extract technologies and programming languages
    jd_prog = []
    for lang in PROGRAMMING_LANGUAGES:
        if re.search(r'\b' + re.escape(lang) + r'\b', jd_lower):
            jd_prog.append(lang.capitalize() if lang not in ["sql", "html", "css", "c++", "c#"] else lang.upper())

    jd_tech = []
    for tool in TOOLS_AND_TECHNOLOGIES:
        if re.search(r'\b' + re.escape(tool) + r'\b', jd_lower):
            jd_tech.append(tool.title() if tool not in ["aws", "gcp", "k8s", "ci/cd", "llm", "rag", "rest api", "sql"] else tool.upper())

    jd_soft = []
    for soft in SOFT_SKILLS:
        if re.search(r'\b' + re.escape(soft) + r'\b', jd_lower):
            jd_soft.append(soft.title())

    combined_all_skills = sorted(list(set(jd_prog + jd_tech + jd_soft)))

    # Distinguish Required vs Preferred skills based on keyword context
    required_skills = []
    preferred_skills = []

    lines = jd_clean.split('\n')
    for line in lines:
        line_lower = line.lower()
        is_pref = any(p in line_lower for p in ["preferred", "nice to have", "plus", "bonus", "desirable", "optional"])
        for skill in combined_all_skills:
            if re.search(r'\b' + re.escape(skill.lower()) + r'\b', line_lower):
                if is_pref:
                    if skill not in preferred_skills:
                        preferred_skills.append(skill)
                else:
                    if skill not in required_skills:
                        required_skills.append(skill)

    # Fallback if no explicit distinction
    if not required_skills:
        required_skills = combined_all_skills
    if not preferred_skills:
        preferred_skills = [s for s in combined_all_skills if s not in required_skills]

    # Extract experience requirements (e.g. "5+ years", "3-5 years")
    exp_matches = re.findall(r'(\d+\+?\s*(?:to|-)?\s*\d*\s*years?(?:\s*of\s*experience)?)', jd_lower)
    exp_req = exp_matches[0].title() if exp_matches else "Experience requirement not explicitly specified."

    # Extract qualification requirement (e.g. Bachelor's, Master's)
    qual_matches = []
    for q in ["bachelor", "master", "phd", "degree", "computer science", "engineering", "b.s.", "m.s."]:
        if q in jd_lower:
            qual_matches.append(q.title())
    qual_req = ", ".join(list(set(qual_matches))) if qual_matches else "Degree in Computer Science or related field."

    jd_keywords = extract_keywords(jd_clean, top_n=30)

    return {
        "raw_text": jd_clean,
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "all_skills": combined_all_skills,
        "programming_languages": jd_prog,
        "technologies": jd_tech,
        "soft_skills": jd_soft,
        "experience_requirements": exp_req,
        "qualifications": qual_req,
        "keywords": jd_keywords
    }


def calculate_resume_job_match(structured_resume: Dict[str, Any], job_desc: str) -> Dict[str, Any]:
    """
    Compares candidate resume with target job description and returns overall
    match score and comprehensive breakdown.
    """
    resume_text = structured_resume.get("raw_text", "")
    jd_info = extract_jd_requirements(job_desc)

    res_skills_lower = set([s.lower() for s in structured_resume.get("technical_skills", []) + structured_resume.get("soft_skills", [])])
    jd_skills_lower = set([s.lower() for s in jd_info["all_skills"]])

    # 1. Skills Match Calculation
    if jd_skills_lower:
        matched_skills_lower = res_skills_lower.intersection(jd_skills_lower)
        missing_skills_lower = jd_skills_lower - res_skills_lower
        skills_score = round((len(matched_skills_lower) / len(jd_skills_lower)) * 100, 1)
    else:
        matched_skills_lower = set()
        missing_skills_lower = set()
        skills_score = 75.0

    # Format matched and missing skills nicely
    matched_skills = sorted([s.title() for s in matched_skills_lower])
    missing_skills = sorted([s.title() for s in missing_skills_lower])

    # 2. Keyword Match Calculation
    res_kw_lower = set([k.lower() for k in structured_resume.get("keywords", [])])
    jd_kw_lower = set([k.lower() for k in jd_info["keywords"]])

    if jd_kw_lower:
        matched_kw_lower = res_kw_lower.intersection(jd_kw_lower)
        missing_kw_lower = jd_kw_lower - res_kw_lower
        keyword_score = round((len(matched_kw_lower) / len(jd_kw_lower)) * 100, 1)
    else:
        matched_kw_lower = set()
        missing_kw_lower = set()
        keyword_score = 70.0

    matching_keywords = sorted([k.capitalize() for k in matched_kw_lower])
    missing_keywords = sorted([k.capitalize() for k in missing_kw_lower])

    # 3. Experience & Qualification Match Score
    res_edu = " ".join(structured_resume.get("education", [])).lower()
    res_exp = " ".join(structured_resume.get("experience", [])).lower()
    jd_lower = job_desc.lower()

    edu_match = False
    if any(degree in jd_lower for degree in ["bachelor", "master", "phd", "degree", "b.s.", "m.s."]):
        if any(degree in res_edu for degree in ["bachelor", "master", "phd", "degree", "b.s.", "m.s.", "university", "college"]):
            edu_match = True
    else:
        edu_match = True  # Not explicitly mandatory in JD

    exp_count = len(structured_resume.get("experience", []))
    if edu_match and (exp_count >= 2 or len(res_exp) > 200):
        exp_qual_score = 90.0
    elif edu_match:
        exp_qual_score = 75.0
    else:
        exp_qual_score = 55.0

    # 4. TF-IDF Cosine Similarity
    tfidf_sim = calculate_tfidf_similarity(resume_text, job_desc)
    tfidf_score = round(tfidf_sim * 100, 1)

    # 5. Composite Overall Match Score Weighting
    # Skills: 40%, Keywords: 20%, Exp/Qual: 20%, Semantic Similarity: 20%
    overall_match_score = round(
        (skills_score * 0.40) +
        (keyword_score * 0.20) +
        (exp_qual_score * 0.20) +
        (tfidf_score * 0.20),
        1
    )

    # Bound within [0, 100]
    overall_match_score = max(0.0, min(100.0, overall_match_score))

    return {
        "overall_score": overall_match_score,
        "skills_score": skills_score,
        "keyword_score": keyword_score,
        "exp_qual_score": exp_qual_score,
        "tfidf_score": tfidf_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "matching_keywords": matching_keywords,
        "missing_keywords": missing_keywords,
        "jd_requirements": jd_info
    }
