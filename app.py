"""
AI Resume Analyzer & Job Match Assistant - Production Application
A local-first, production-ready AI application that extracts resume text from PDFs,
analyzes candidate-job fit, computes multi-dimensional ATS match scores, detects missing sakills/keywords,
provides deep Google Gemini AI feedback, and generates personalized professional cover letters.
"""

import os
import streamlit as st
import pandas as pd
import altair as alt
from dotenv import load_dotenv

# Requirement 2 & 3: Explicitly locate project-root .env file relative to app.py location
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
ENV_FILE_PATH = os.path.join(PROJECT_ROOT, ".env")
ENV_TXT_FILE_PATH = os.path.join(PROJECT_ROOT, ".env.txt")

if os.path.exists(ENV_FILE_PATH):
    load_dotenv(dotenv_path=ENV_FILE_PATH, override=True)
elif os.path.exists(ENV_TXT_FILE_PATH):
    load_dotenv(dotenv_path=ENV_TXT_FILE_PATH, override=True)
else:
    load_dotenv(override=True)

# Import custom styling and sample data presets
from styles import apply_custom_styles
from sample_data import SAMPLE_RESUMES, SAMPLE_JOB_DESCRIPTIONS

# Import modular backend functions from utils
from utils.resume_parser import (
    validate_and_extract_pdf,
    extract_structured_resume,
    clean_text
)
from utils.matching import (
    calculate_resume_job_match,
    extract_jd_requirements
)
from utils.analyzer import (
    analyze_strengths_and_weaknesses,
    analyze_ats_compatibility,
    generate_improvement_suggestions
)
from utils.gemini_service import (
    get_gemini_api_key,
    is_gemini_configured,
    generate_ai_resume_feedback,
    generate_cover_letter
)


# --- STREAMLIT PAGE CONFIGURATION ---
st.set_page_config(
    page_title="AI Resume Analyzer & Job Match Assistant",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom modern CSS styling
apply_custom_styles()


# --- INITIALIZE SESSION STATE ---
if "resume_text" not in st.session_state:
    st.session_state["resume_text"] = ""
if "job_desc" not in st.session_state:
    st.session_state["job_desc"] = ""
if "structured_resume" not in st.session_state:
    st.session_state["structured_resume"] = None
if "match_results" not in st.session_state:
    st.session_state["match_results"] = None
if "resume_filename" not in st.session_state:
    st.session_state["resume_filename"] = "Uploaded_Resume.pdf"
if "ai_feedback" not in st.session_state:
    st.session_state["ai_feedback"] = None
if "cover_letter_text" not in st.session_state:
    st.session_state["cover_letter_text"] = ""


# --- SIDEBAR CONTROL PANEL ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/artificial-intelligence.png", width=56)
    st.title("🎯 Control Panel")
    st.markdown("---")

    # 1. Quick Load Sample Data (For Students / Demos)
    st.subheader("⚡ Quick Demo Presets")
    st.caption("Load a pre-configured role to test the app in 1 click:")
    sample_choice = st.selectbox(
        "Select Role Preset:",
        ["-- Select Preset --", "AI / ML Engineer", "Full Stack Developer", "Product Manager"],
        help="Instantly populates a sample PDF resume and matching job description."
    )

    if sample_choice != "-- Select Preset --":
        if st.button("📥 Load Preset Data", key="btn_load_sample", type="secondary", use_container_width=True):
            res_sample = SAMPLE_RESUMES[sample_choice]
            jd_key = (
                "Senior AI / ML Engineer" if sample_choice == "AI / ML Engineer"
                else ("Full Stack React / Python Developer" if sample_choice == "Full Stack Developer" else "Product Manager (B2B SaaS)")
            )
            jd_sample = SAMPLE_JOB_DESCRIPTIONS[jd_key]

            st.session_state["resume_text"] = res_sample
            st.session_state["job_desc"] = jd_sample
            st.session_state["resume_filename"] = f"Sample_{sample_choice.replace(' ', '_')}.pdf"
            st.session_state["structured_resume"] = extract_structured_resume(res_sample, st.session_state["resume_filename"])
            st.session_state["match_results"] = None
            st.session_state["ai_feedback"] = None
            st.session_state["cover_letter_text"] = ""
            st.success(f"Loaded '{sample_choice}' preset!")
            st.rerun()

    st.markdown("---")

    # 2. Gemini API Key Settings
    st.subheader("🔑 Google Gemini API Key")
    
    # Requirement 8: Check for .env API key
    env_gemini_key = get_gemini_api_key()

    # Requirement 6: Sidebar input widget
    sidebar_api_key_input = st.text_input(
        "Gemini API Key:",
        value="",
        type="password",
        key="sidebar_gemini_api_key",
        placeholder="Loaded from .env automatically (or paste key here)...",
        help="Key is loaded automatically from your project-root .env file (GEMINI_API_KEY=...). You can also paste a key here to override."
    )

    # Requirement 7 & 8: If sidebar key entered, use sidebar key; otherwise use .env key
    if sidebar_api_key_input and sidebar_api_key_input.strip():
        active_key = sidebar_api_key_input.strip()
    else:
        active_key = env_gemini_key

    # Requirement 12: Accurate status message
    if active_key and len(active_key) > 5:
        st.success("✨ Gemini 2.5 AI Mode Active")
    else:
        st.info("ℹ️ Local Smart NLP Engine Active")
        st.caption("👉 Add `GEMINI_API_KEY=your_key` to `.env` file or paste key above to enable Gemini AI.")

    st.markdown("---")
    
    # Reset/Clear Button
    if st.button("🔄 Clear / Reset All Data", key="btn_reset_sidebar", use_container_width=True):
        st.session_state["resume_text"] = ""
        st.session_state["job_desc"] = ""
        st.session_state["structured_resume"] = None
        st.session_state["match_results"] = None
        st.session_state["ai_feedback"] = None
        st.session_state["cover_letter_text"] = ""
        st.rerun()

    st.caption("AI Resume Analyzer v4.0 • Python + spaCy + Gemini")


# --- HERO HEADER ---
st.markdown("""
<div class="hero-container">
    <div class="hero-title">AI Resume Analyzer & Job Match Assistant</div>
    <div class="hero-subtitle">
        Upload your PDF resume, paste target job description, extract candidate skills, 
        calculate ATS match scores, discover missing keywords, and generate custom cover letters.
    </div>
    <div class="hero-badges">
        <span class="feature-badge">⚡ Local NLP & Scikit-Learn</span>
        <span class="feature-badge">📄 PDF Text Extraction</span>
        <span class="feature-badge">🤖 Gemini 2.5 AI Feedback</span>
        <span class="feature-badge">✉️ Personalized Cover Letter</span>
    </div>
</div>
""", unsafe_allow_html=True)


# --- GEMINI API NOTICE BANNER ---
if not active_key:
    st.warning("""
    **ℹ️ Gemini API Key Notice:** No `GEMINI_API_KEY` configured. 
    The app is running in **Local Smart NLP Engine Mode**. All match scores, skill extractions, keyword gaps, and cover letter templates are fully functional out-of-the-box! 
    *To enable deep Gemini AI analysis, set `GEMINI_API_KEY=your_key` in `.env` file or enter your key in the sidebar.*
    """)


# --- MAIN INPUT SECTION (2 COLUMNS) ---
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.subheader("1. 📄 Upload Candidate Resume (PDF)")
    uploaded_file = st.file_uploader(
        "Upload Resume (.pdf format)",
        type=["pdf"],
        help="Upload candidate PDF resume for text & skill extraction."
    )

    if uploaded_file is not None:
        is_valid, msg, extracted_text, page_count = validate_and_extract_pdf(uploaded_file)
        if is_valid:
            st.session_state["resume_text"] = extracted_text
            st.session_state["resume_filename"] = uploaded_file.name
            st.session_state["structured_resume"] = extract_structured_resume(extracted_text, uploaded_file.name)
            st.success(f"✅ {msg}")
        else:
            st.error(f"❌ {msg}")
            st.session_state["resume_text"] = ""
            st.session_state["structured_resume"] = None

    # Text Area Preview / Manual Edit
    resume_input_text = st.text_area(
        "Extracted Resume Text Preview & Editor:",
        value=st.session_state.get("resume_text", ""),
        height=220,
        placeholder="Extracted PDF text will appear here automatically, or paste resume text manually..."
    )
    if resume_input_text != st.session_state.get("resume_text", ""):
        st.session_state["resume_text"] = resume_input_text
        if resume_input_text.strip():
            st.session_state["structured_resume"] = extract_structured_resume(resume_input_text, st.session_state["resume_filename"])
        else:
            st.session_state["structured_resume"] = None

    if st.session_state.get("resume_text", "").strip():
        word_cnt = len(st.session_state["resume_text"].split())
        st.caption(f"📊 Extracted Resume: {word_cnt} words")

with col_right:
    st.subheader("2. 🎯 Target Job Description")
    jd_input_text = st.text_area(
        "Paste Job Description below:",
        value=st.session_state.get("job_desc", ""),
        height=320,
        placeholder="Paste full target job description, required skills, and qualifications here..."
    )
    st.session_state["job_desc"] = jd_input_text

    if jd_input_text.strip():
        jd_word_cnt = len(jd_input_text.split())
        st.caption(f"📊 Job Description: {jd_word_cnt} words")


# --- MAIN CONTROL BUTTONS TOOLBAR ---
st.markdown("<br>", unsafe_allow_html=True)
b_col1, b_col2, b_col3, b_col4 = st.columns([2, 2, 2, 1])

with b_col1:
    btn_analyze = st.button("🚀 Analyze Resume", type="primary", use_container_width=True)
with b_col2:
    btn_suggestions = st.button("🤖 Generate AI Suggestions", use_container_width=True)
with b_col3:
    btn_cover_top = st.button("✉️ Generate Cover Letter", use_container_width=True)
with b_col4:
    if st.button("🔄 Clear", key="btn_clear_toolbar", use_container_width=True):
        st.session_state["resume_text"] = ""
        st.session_state["job_desc"] = ""
        st.session_state["structured_resume"] = None
        st.session_state["match_results"] = None
        st.session_state["ai_feedback"] = None
        st.session_state["cover_letter_text"] = ""
        st.rerun()


# --- ANALYSIS EXECUTION LOGIC ---
res_text = st.session_state.get("resume_text", "").strip()
jd_text = st.session_state.get("job_desc", "").strip()

if btn_analyze or btn_suggestions or btn_cover_top:
    if not res_text:
        st.error("⚠️ Please upload a PDF resume or enter resume text before proceeding.")
    elif not jd_text:
        st.error("⚠️ Please enter or paste target job description before proceeding.")
    else:
        with st.spinner("🔍 Running Resume Information Extraction & Match Analysis..."):
            struct_res = extract_structured_resume(res_text, st.session_state.get("resume_filename", "Resume.pdf"))
            st.session_state["structured_resume"] = struct_res

            match_data = calculate_resume_job_match(struct_res, jd_text)
            sw_data = analyze_strengths_and_weaknesses(struct_res, match_data)
            ats_data = analyze_ats_compatibility(struct_res, jd_text)
            local_suggestions = generate_improvement_suggestions(struct_res, match_data, jd_text)

            ai_feedback = generate_ai_resume_feedback(struct_res, jd_text, match_data, custom_key=active_key)

            st.session_state["match_results"] = {
                "match": match_data,
                "sw": sw_data,
                "ats": ats_data,
                "local_suggestions": local_suggestions
            }
            st.session_state["ai_feedback"] = ai_feedback

            if btn_cover_top or "cover_letter_text" not in st.session_state or not st.session_state["cover_letter_text"]:
                cover_letter = generate_cover_letter(
                    structured_resume=struct_res,
                    job_desc=jd_text,
                    company_name="Hiring Team",
                    target_role="Target Role",
                    custom_key=active_key
                )
                st.session_state["cover_letter_text"] = cover_letter

            st.success("✅ Analysis Complete!")


# --- RESULTS DASHBOARD ---
if st.session_state.get("match_results") is not None:
    results = st.session_state["match_results"]
    match = results["match"]
    struct_res = st.session_state["structured_resume"]
    ai_fb = st.session_state.get("ai_feedback", {})

    st.markdown("---")
    st.header("📊 Results & Insights Dashboard")

    # 5 SEPARATE UI TABS
    tab_analysis, tab_match, tab_missing, tab_suggestions, tab_cover = st.tabs([
        "📋 Resume Analysis",
        "📊 Match Results",
        "🎯 Missing Skills & Keywords",
        "🤖 AI Suggestions & ATS Advice",
        "✉️ Cover Letter"
    ])

    # TAB 1: RESUME ANALYSIS
    with tab_analysis:
        st.subheader(f"👤 Candidate Profile: {struct_res.get('name', 'Candidate')}")
        
        info_col1, info_col2, info_col3 = st.columns(3)
        with info_col1:
            st.markdown(f"**Candidate Name:** {struct_res.get('name')}")
        with info_col2:
            st.markdown(f"**Email Address:** {struct_res.get('email')}")
        with info_col3:
            st.markdown(f"**Phone Number:** {struct_res.get('phone')}")

        st.markdown("---")
        sec_col1, sec_col2 = st.columns(2)

        with sec_col1:
            st.markdown("#### 💻 Technical Skills")
            tech_s = struct_res.get("technical_skills", [])
            st.write(", ".join(tech_s) if tech_s else "No technical skills extracted.")

            st.markdown("#### 🛠️ Programming Languages & Tools")
            prog_s = struct_res.get("programming_languages", [])
            tools_s = struct_res.get("tools_and_tech", [])
            all_tools = sorted(list(set(prog_s + tools_s)))
            st.write(", ".join(all_tools) if all_tools else "No specific languages/tools extracted.")

            st.markdown("#### 🗣️ Soft Skills")
            soft_s = struct_res.get("soft_skills", [])
            st.write(", ".join(soft_s) if soft_s else "No soft skills extracted.")

        with sec_col2:
            st.markdown("#### 🎓 Education Background")
            for edu_item in struct_res.get("education", []):
                st.markdown(f"• {edu_item}")

            st.markdown("#### 🏅 Certifications")
            for cert_item in struct_res.get("certifications", []):
                st.markdown(f"• {cert_item}")

            if struct_res.get("projects"):
                st.markdown("#### 📁 Projects")
                for proj_item in struct_res.get("projects", []):
                    st.markdown(f"• {proj_item}")

        st.markdown("---")
        st.markdown("#### 💼 Extracted Work Experience Bullet Points")
        for exp_item in struct_res.get("experience", []):
            st.markdown(f"• {exp_item}")

    # TAB 2: MATCH RESULTS
    with tab_match:
        overall_score = match["overall_score"]
        if overall_score >= 75:
            score_color = "#10b981"
            score_label = "Excellent Fit"
        elif overall_score >= 55:
            score_color = "#f59e0b"
            score_label = "Moderate Match"
        else:
            score_color = "#ef4444"
            score_label = "Low Match"

        # Metric Cards Row
        mc1, mc2, mc3, mc4 = st.columns(4)
        with mc1:
            st.markdown(f"""
            <div class="metric-card" style="border-top: 4px solid {score_color};">
                <div class="metric-label">Overall Match Score</div>
                <div class="metric-value" style="color: {score_color};">{overall_score}%</div>
                <div class="metric-sub" style="color: {score_color};">{score_label}</div>
            </div>
            """, unsafe_allow_html=True)
        with mc2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Skills Match Score</div>
                <div class="metric-value">{match['skills_score']}%</div>
                <div class="metric-sub">{len(match['matched_skills'])} / {len(match['jd_requirements']['all_skills'])} Skills</div>
            </div>
            """, unsafe_allow_html=True)
        with mc3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Keyword Similarity Score</div>
                <div class="metric-value">{match['keyword_score']}%</div>
                <div class="metric-sub">{len(match['matching_keywords'])} Terms Overlap</div>
            </div>
            """, unsafe_allow_html=True)
        with mc4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Exp & Qual Score</div>
                <div class="metric-value">{match['exp_qual_score']}%</div>
                <div class="metric-sub">ATS Score: {results['ats']['ats_score']}%</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📊 Score Weighting & Breakdown Chart")

        # Altair Bar Chart
        df_scores = pd.DataFrame({
            "Category": ["Skills Match (40%)", "Keyword Overlap (20%)", "Exp & Qualifications (20%)", "Semantic TF-IDF (20%)"],
            "Score": [match['skills_score'], match['keyword_score'], match['exp_qual_score'], match['tfidf_score']]
        })
        chart = alt.Chart(df_scores).mark_bar(cornerRadiusEnd=6, size=24).encode(
            x=alt.X("Score:Q", scale=alt.Scale(domain=[0, 100]), title="Score (%)"),
            y=alt.Y("Category:N", sort=None, title="Evaluation Category"),
            color=alt.Color("Score:Q", scale=alt.Scale(scheme="purples"), legend=None)
        ).properties(height=200)
        st.altair_chart(chart, use_container_width=True)

    # TAB 3: MISSING SKILLS & KEYWORDS
    with tab_missing:
        st.subheader("🎯 Skill & Keyword Gap Analysis")

        sk_col1, sk_col2 = st.columns(2)

        with sk_col1:
            st.markdown("#### ✅ Matched Skills (Present on Resume)")
            if match["matched_skills"]:
                badges_html = " ".join([f'<span class="badge-matched">✓ {s}</span>' for s in match["matched_skills"]])
                st.markdown(f'<div class="badge-container">{badges_html}</div>', unsafe_allow_html=True)
            else:
                st.info("No direct skill matches detected.")

            st.markdown("#### 🔍 Matching Keywords")
            if match["matching_keywords"]:
                kw_html = " ".join([f'<span class="badge-extra"># {k}</span>' for k in match["matching_keywords"]])
                st.markdown(f'<div class="badge-container">{kw_html}</div>', unsafe_allow_html=True)
            else:
                st.info("No matching key terms found.")

        with sk_col2:
            st.markdown("#### ⚠️ Missing Required Skills")
            missing_sk = ai_fb.get("missing_skills") or match["missing_skills"]
            if missing_sk:
                missing_html = " ".join([f'<span class="badge-missing">✗ {s}</span>' for s in missing_sk])
                st.markdown(f'<div class="badge-container">{missing_html}</div>', unsafe_allow_html=True)
            else:
                st.success("🎉 All target job skills are present on your resume!")

            st.markdown("#### ❗ Missing Important Job Keywords")
            missing_kw = ai_fb.get("missing_keywords") or match["missing_keywords"]
            if missing_kw:
                missing_kw_html = " ".join([f'<span class="badge-missing">! {k}</span>' for k in missing_kw[:15]])
                st.markdown(f'<div class="badge-container">{missing_kw_html}</div>', unsafe_allow_html=True)
            else:
                st.success("🎉 All key job description terms are present!")

        st.markdown("---")
        st.subheader("📋 Structured Skills & Keywords Comparison Table")
        
        # Build pandas tables for matched vs missing skills
        matched_df_list = [{"Skill / Keyword": s, "Status": "Matched ✅", "Category": "Skill"} for s in match["matched_skills"]]
        missing_df_list = [{"Skill / Keyword": s, "Status": "Missing ⚠️", "Category": "Skill"} for s in missing_sk]
        missing_kw_list = [{"Skill / Keyword": k, "Status": "Missing Keyword ❗", "Category": "Domain Keyword"} for k in missing_kw[:10]]
        
        combined_skills_df = pd.DataFrame(matched_df_list + missing_df_list + missing_kw_list)
        if not combined_skills_df.empty:
            st.dataframe(combined_skills_df, use_container_width=True, hide_index=True)

    # TAB 4: AI SUGGESTIONS & ATS ADVICE
    with tab_suggestions:
        st.subheader("🤖 AI Resume Feedback & ATS Optimization Plan")
        if ai_fb.get("notice"):
            st.caption(ai_fb["notice"])

        # Strengths & Weaknesses
        st_col, wk_col = st.columns(2)
        with st_col:
            st.markdown("#### 💪 Resume Strengths")
            for str_item in ai_fb.get("strengths", []):
                st.markdown(f"""
                <div class="check-item">
                    <span class="check-icon-pass">✓</span>
                    <div>{str_item}</div>
                </div>
                """, unsafe_allow_html=True)

        with wk_col:
            st.markdown("#### ⚠️ Resume Weaknesses & Gaps")
            for weak_item in ai_fb.get("weaknesses", []):
                st.markdown(f"""
                <div class="check-item">
                    <span class="check-icon-fail">✗</span>
                    <div>{weak_item}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

        # Categorized Suggestions Tabs
        sug_t1, sug_t2, sug_t3, sug_t4 = st.tabs([
            "📝 Professional Summary Suggestions",
            "🚀 Project Descriptions & Bullet Metrics",
            "🛠️ Skills Section Optimization",
            "🎯 ATS Keyword & Formatting Advice"
        ])

        with sug_t1:
            st.markdown("#### Suggestions for Professional Summary")
            for item in ai_fb.get("suggestions_summary", []):
                st.markdown(f"• {item}")

        with sug_t2:
            st.markdown("#### Suggestions for Improving Project & Experience Descriptions")
            for item in ai_fb.get("suggestions_projects", []):
                st.markdown(f"• {item}")

        with sug_t3:
            st.markdown("#### Suggestions for Skills Section")
            for item in ai_fb.get("suggestions_skills_section", []):
                st.markdown(f"• {item}")

        with sug_t4:
            st.markdown("#### Practical ATS-Friendly Formatting & Keyword Suggestions")
            for item in ai_fb.get("suggestions_ats", []):
                st.markdown(f"• {item}")

    # TAB 5: COVER LETTER
    with tab_cover:
        st.subheader("✉️ Personalized Professional Cover Letter Generator")
        st.caption("Generate a tailored cover letter based specifically on your candidate resume and target job description.")

        cl_input_col1, cl_input_col2 = st.columns(2)
        with cl_input_col1:
            target_role_name = st.text_input("Target Job Title:", value="Software Engineer", key="input_target_role")
        with cl_input_col2:
            target_company_name = st.text_input("Company Name:", value="Tech Innovations Inc", key="input_company_name")

        if st.button("✨ Generate Personalized Cover Letter", type="primary", key="btn_gen_cover_tab"):
            with st.spinner("✍️ Writing tailored cover letter with Gemini AI..."):
                cl_text = generate_cover_letter(
                    structured_resume=struct_res,
                    job_desc=jd_text,
                    company_name=target_company_name,
                    target_role=target_role_name,
                    custom_key=active_key
                )
                st.session_state["cover_letter_text"] = cl_text
                st.success("✅ Cover Letter Generated!")

        if st.session_state.get("cover_letter_text"):
            st.markdown("---")
            st.subheader("📄 Generated Cover Letter")
            
            cover_output = st.session_state["cover_letter_text"]
            st.text_area("Cover Letter Output (Easy to copy):", value=cover_output, height=400, key="cl_final_display")

            dl_col1, dl_col2 = st.columns([1, 4])
            with dl_col1:
                st.download_button(
                    label="📥 Download Cover Letter (.txt)",
                    data=cover_output,
                    file_name=f"Cover_Letter_{struct_res.get('name', 'Candidate').replace(' ', '_')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )


# --- FOOTER ---
st.markdown("""
<div class="footer-text">
    AI Resume Analyzer and Job Match Assistant • Powered by Python, Streamlit, spaCy & Google Gemini API
</div>
""", unsafe_allow_html=True)
