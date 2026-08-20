"""
Structured Resume Parser Module
Extracts candidate name, contact details, skills, programming languages,
tools & tech, education, work experience, certifications, projects, and keywords from PDF resumes.
Includes spaCy NLP processing with automatic fallback to pattern matching.
"""

import io
import re
from typing import Dict, List, Set, Tuple, Any

import PyPDF2

# Attempt spaCy import and model load with graceful fallback
nlp = None
try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
    except Exception:
        try:
            nlp = spacy.blank("en")
        except Exception:
            nlp = None
except ImportError:
    nlp = None

# Comprehensive Taxonomy Lists
PROGRAMMING_LANGUAGES = {
    "python", "javascript", "typescript", "java", "c++", "c#", "c", "go", "golang",
    "rust", "ruby", "php", "swift", "kotlin", "scala", "r", "matlab", "bash", "shell",
    "sql", "html", "css", "dart", "perl", "haskell", "assembly"
}

TOOLS_AND_TECHNOLOGIES = {
    "react", "react.js", "next.js", "vue", "vue.js", "angular", "svelte", "tailwind css",
    "bootstrap", "redux", "node.js", "express", "fastapi", "django", "flask", "spring",
    "spring boot", "rest api", "graphql", "grpc", "microservices", "postgresql", "mysql",
    "mongodb", "sqlite", "redis", "elasticsearch", "cassandra", "dynamodb", "snowflake",
    "bigquery", "apache spark", "spark", "kafka", "airflow", "dbt", "pandas", "numpy",
    "scipy", "scikit-learn", "pytorch", "tensorflow", "keras", "opencv", "hugging face",
    "transformers", "langchain", "llamaindex", "rag", "llm", "large language models",
    "prompt engineering", "vector databases", "chromadb", "pinecone", "faiss", "aws",
    "azure", "gcp", "docker", "kubernetes", "k8s", "terraform", "ansible", "jenkins",
    "github actions", "ci/cd", "git", "github", "gitlab", "jira", "postman", "jest",
    "cypress", "pytest", "selenium", "figma", "tableau", "power bi", "mixpanel"
}

SOFT_SKILLS = {
    "leadership", "communication", "problem solving", "teamwork", "collaboration",
    "critical thinking", "time management", "adaptability", "project management",
    "stakeholder management", "analytical skills", "mentorship", "creativity",
    "decision making", "conflict resolution", "negotiation", "organization"
}

COMMON_CERTIFICATIONS = {
    "aws certified", "aws certified developer", "aws certified solutions architect",
    "aws certified machine learning", "azure certified", "gcp certified",
    "certified scrum master", "csm", "cspo", "pmp", "cissp", "ceh", "comptia",
    "google cloud certified", "tensorflow developer", "ckad", "cka", "hashicorp certified",
    "oracle certified", "microsoft certified"
}

DEGREE_PATTERNS = [
    r"(?i)\b(bachelor['’]?s?|b\.s\.|b\.a\.|b\.tech|b\.e\.|b\.sc|bba)\b",
    r"(?i)\b(master['’]?s?|m\.s\.|m\.a\.|m\.tech|m\.e\.|m\.sc|mba)\b",
    r"(?i)\b(ph\.?d|doctorate|doctor of philosophy)\b",
    r"(?i)\b(associate['’]?s?|a\.s\.|a\.a\.)\b",
    r"(?i)\b(degree in|diploma in|major in)\b"
]


def clean_text(text: str) -> str:
    """Clean and normalize extracted text."""
    if not text:
        return ""
    # Normalize line breaks & tabs
    text = re.sub(r'[\r\t]+', ' ', text)
    # Remove non-printable characters while preserving standard punctuation
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    # Remove duplicate blank lines
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    return '\n'.join(lines)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract readable text from PDF byte content using PyPDF2.
    Handles corrupt/encrypted files gracefully.
    """
    text = ""
    try:
        pdf_file = io.BytesIO(file_bytes)
        reader = PyPDF2.PdfReader(pdf_file)
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception:
                return "Error: The uploaded PDF is password-protected or encrypted."

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    except Exception as e:
        return f"Error reading PDF file: {str(e)}"
    
    return clean_text(text)


def validate_and_extract_pdf(uploaded_file) -> Tuple[bool, str, str, int]:
    """
    Validates uploaded PDF file and extracts text using PyPDF2.
    Returns: (is_valid: bool, status_message: str, extracted_text: str, page_count: int)
    """
    if uploaded_file is None:
        return False, "No file uploaded. Please upload a PDF resume.", "", 0

    filename = getattr(uploaded_file, "name", "uploaded_resume.pdf")
    if not filename.lower().endswith(".pdf"):
        return False, f"Invalid format '{filename}'. Only PDF resumes (.pdf) are supported.", "", 0

    try:
        file_bytes = uploaded_file.getvalue() if hasattr(uploaded_file, "getvalue") else uploaded_file.read()
        if len(file_bytes) == 0:
            return False, f"File '{filename}' is empty (0 bytes).", "", 0

        pdf_file = io.BytesIO(file_bytes)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        page_count = len(pdf_reader.pages)

        if page_count == 0:
            return False, f"PDF file '{filename}' contains 0 pages.", "", 0

        extracted_text = ""
        for page in pdf_reader.pages:
            t = page.extract_text()
            if t:
                extracted_text += t + "\n"

        extracted_text = clean_text(extracted_text)

        if not extracted_text or len(extracted_text.strip()) < 30:
            return False, f"PDF file '{filename}' appears to be empty, scanned, or unreadable.", "", page_count

        return True, f"Successfully extracted text from '{filename}' ({page_count} page(s)).", extracted_text, page_count

    except Exception as e:
        return False, f"Could not read PDF '{filename}': {str(e)}", "", 0


def extract_name(text: str) -> str:
    """Extract candidate name from the top of the resume using spaCy or regex."""
    if not text:
        return "Candidate Name"

    first_few_lines = [line.strip() for line in text.split("\n")[:10] if line.strip()]
    if not first_few_lines:
        return "Candidate Name"

    # 1. Try spaCy PERSON NER if available
    if nlp:
        try:
            doc = nlp("\n".join(first_few_lines[:5]))
            for ent in doc.ents:
                if ent.label_ == "PERSON" and 2 <= len(ent.text.split()) <= 4:
                    cleaned_person = re.sub(r'[^a-zA-Z\s\.]', '', ent.text).strip()
                    if cleaned_person and not any(kw in cleaned_person.lower() for kw in ["resume", "curriculum", "page", "email", "phone"]):
                        return cleaned_person.title()
        except Exception:
            pass

    # 2. Regex fallback: First non-contact line with 2-4 words
    for line in first_few_lines:
        line_clean = re.sub(r'[^a-zA-Z\s\.]', '', line).strip()
        words = line_clean.split()
        if 2 <= len(words) <= 4:
            lower_line = line_clean.lower()
            if not any(kw in lower_line for kw in ["resume", "cv", "curriculum", "engineer", "developer", "manager", "summary", "contact", "experience"]):
                return line_clean.title()

    return first_few_lines[0].title() if first_few_lines else "Candidate Name"


def extract_email(text: str) -> str:
    """Extract candidate email using regex."""
    match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    return match.group(0) if match else "Not specified"


def extract_phone(text: str) -> str:
    """Extract candidate phone number using regex."""
    match = re.search(r'(\+?\d{1,3}[\s\-]?)?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4}', text)
    return match.group(0) if match else "Not specified"


def extract_programming_languages(text: str) -> List[str]:
    """Extract programming languages found in text."""
    found = set()
    text_lower = text.lower()
    for lang in PROGRAMMING_LANGUAGES:
        # Match exact word boundaries
        pattern = r'\b' + re.escape(lang) + r'\b'
        if re.search(pattern, text_lower):
            found.add(lang.capitalize() if lang not in ["sql", "html", "css", "c++", "c#"] else lang.upper())
    return sorted(list(found))


def extract_tools_and_tech(text: str) -> List[str]:
    """Extract tools and technologies found in text."""
    found = set()
    text_lower = text.lower()
    for tool in TOOLS_AND_TECHNOLOGIES:
        pattern = r'\b' + re.escape(tool) + r'\b'
        if re.search(pattern, text_lower):
            # Format nicely
            found.add(tool.title() if tool not in ["aws", "gcp", "k8s", "ci/cd", "llm", "rag", "rest api", "sql"] else tool.upper())
    return sorted(list(found))


def extract_soft_skills(text: str) -> List[str]:
    """Extract soft skills found in text."""
    found = set()
    text_lower = text.lower()
    for skill in SOFT_SKILLS:
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            found.add(skill.title())
    return sorted(list(found))


def extract_education(text: str) -> List[str]:
    """Extract education background, degrees, and institutions."""
    lines = text.split('\n')
    education_entries = []
    in_edu_section = False

    for line in lines:
        line_clean = line.strip()
        line_lower = line_clean.lower()

        if any(h in line_lower for h in ["education", "academic qualification", "academic background", "degrees"]):
            in_edu_section = True
            continue
        elif in_edu_section and any(h in line_lower for h in ["experience", "work history", "skills", "projects", "certifications"]):
            in_edu_section = False
            continue

        if in_edu_section and line_clean:
            education_entries.append(line_clean)
        elif not in_edu_section:
            for pattern in DEGREE_PATTERNS:
                if re.search(pattern, line_clean):
                    education_entries.append(line_clean)
                    break

    if not education_entries:
        # Scan full text for degrees
        for line in lines:
            for pattern in DEGREE_PATTERNS:
                if re.search(pattern, line):
                    education_entries.append(line.strip())
                    break

    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for item in education_entries:
        if item.lower() not in seen:
            seen.add(item.lower())
            deduped.append(item)

    return deduped[:5] if deduped else ["Degree / Education details extracted from text."]


def extract_experience(text: str) -> List[str]:
    """Extract work experience entries and bullet points."""
    lines = text.split('\n')
    exp_entries = []
    in_exp_section = False

    for line in lines:
        line_clean = line.strip()
        line_lower = line_clean.lower()

        if any(h in line_lower for h in ["experience", "work history", "employment history", "professional experience", "career"]):
            in_exp_section = True
            continue
        elif in_exp_section and any(h in line_lower for h in ["education", "skills", "projects", "certifications", "academic"]):
            in_exp_section = False
            continue

        if in_exp_section and line_clean:
            exp_entries.append(line_clean)

    if not exp_entries:
        # Return summary lines that look like work experience
        exp_entries = [line.strip() for line in lines if any(k in line.lower() for k in ["developer", "engineer", "manager", "specialist", "analyst", "lead", "architect"])]

    return exp_entries[:12] if exp_entries else ["Professional Work Experience entries extracted."]


def extract_certifications(text: str) -> List[str]:
    """Extract professional certifications from text."""
    found = set()
    text_lower = text.lower()
    for cert in COMMON_CERTIFICATIONS:
        if cert in text_lower:
            found.add(cert.title())

    lines = text.split('\n')
    in_cert_section = False
    for line in lines:
        line_lower = line.lower().strip()
        if any(h in line_lower for h in ["certification", "certificates", "licenses", "credentials"]):
            in_cert_section = True
            continue
        elif in_cert_section and any(h in line_lower for h in ["education", "experience", "skills", "projects"]):
            in_cert_section = False
            continue
        if in_cert_section and line.strip():
            found.add(line.strip())

    return sorted(list(found)) if found else ["Standard Certifications / Training"]


def extract_projects(text: str) -> List[str]:
    """Extract projects from text."""
    lines = text.split('\n')
    projects = []
    in_proj_section = False

    for line in lines:
        line_clean = line.strip()
        line_lower = line_clean.lower()

        if any(h in line_lower for h in ["projects", "key projects", "personal projects", "portfolio"]):
            in_proj_section = True
            continue
        elif in_proj_section and any(h in line_lower for h in ["education", "experience", "skills", "certifications"]):
            in_proj_section = False
            continue

        if in_proj_section and line_clean:
            projects.append(line_clean)

    return projects[:8] if projects else ["Key Portfolio Projects"]


def extract_keywords(text: str, top_n: int = 25) -> List[str]:
    """Extract top domain keywords and terms using NLP or token frequency."""
    if not text:
        return []

    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    stop_words = {
        "and", "the", "for", "with", "that", "this", "from", "have", "were", "been",
        "their", "which", "will", "would", "could", "should", "about", "into", "through",
        "during", "before", "after", "above", "below", "these", "those", "over", "under",
        "again", "further", "then", "once", "here", "there", "when", "where", "why",
        "how", "all", "any", "both", "each", "few", "more", "most", "other", "some",
        "such", "no", "nor", "not", "only", "own", "same", "than", "too", "very",
        "can", "just", "should", "now", "using", "work", "experience", "years", "team",
        "project", "developed", "building", "working", "strong", "ability", "role"
    }

    filtered = [w for w in words if w not in stop_words and len(w) > 2]
    
    # Calculate word counts
    freq: Dict[str, int] = {}
    for w in filtered:
        freq[w] = freq.get(w, 0) + 1

    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [w[0].capitalize() for w in sorted_words[:top_n]]


def extract_structured_resume(resume_text: str, filename: str = "Resume.pdf") -> Dict[str, Any]:
    """
    Parses full resume text into structured fields:
    Name, Email, Phone, Programming Languages, Tools & Tech, Soft Skills,
    Technical Skills, Education, Experience, Certifications, Projects, and Keywords.
    """
    clean_raw = clean_text(resume_text)
    name = extract_name(clean_raw)
    email = extract_email(clean_raw)
    phone = extract_phone(clean_raw)

    prog_langs = extract_programming_languages(clean_raw)
    tools_tech = extract_tools_and_tech(clean_raw)
    soft_skills = extract_soft_skills(clean_raw)
    
    combined_tech_skills = sorted(list(set(prog_langs + tools_tech)))
    education = extract_education(clean_raw)
    experience = extract_experience(clean_raw)
    certifications = extract_certifications(clean_raw)
    projects = extract_projects(clean_raw)
    keywords = extract_keywords(clean_raw, top_n=25)

    return {
        "filename": filename,
        "raw_text": clean_raw,
        "name": name,
        "email": email,
        "phone": phone,
        "programming_languages": prog_langs,
        "tools_and_tech": tools_tech,
        "technical_skills": combined_tech_skills,
        "soft_skills": soft_skills,
        "education": education,
        "experience": experience,
        "certifications": certifications,
        "projects": projects,
        "keywords": keywords,
        "word_count": len(clean_raw.split()) if clean_raw else 0
    }
