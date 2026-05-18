import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
from parser import parse_resume
from ner import analyze_resume
from scorer import compute_tfidf_score, compute_final_score, rank_candidates
from skills_list import SKILLS

# Page configuration
st.set_page_config(
    page_title="AI Resume Shortlister",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling
custom_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* {
    font-family: 'Inter', sans-serif;
}

body,
[data-testid="stAppViewContainer"] {
    background: linear-gradient(180deg, #eef2ff 0%, #f8fafc 100%);
}

[data-testid="stSidebar"] {
    background: #0f172a;
    color: #e2e8f0;
    border-right: 1px solid rgba(148, 163, 184, 0.18);
}

[data-testid="stSidebar"] .stMarkdown {
    color: #cbd5e1;
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4,
[data-testid="stSidebar"] h5,
[data-testid="stSidebar"] p {
    color: #f8fafc;
}

.stApp {
    color: #0f172a;
}

.page-hero {
    background: linear-gradient(135deg, #0f172a 0%, #2563eb 100%);
    color: #ffffff;
    padding: 32px;
    border-radius: 24px;
    margin-bottom: 24px;
    box-shadow: 0 30px 60px rgba(15, 23, 42, 0.14);
    animation: fadeInUp 0.8s ease-out;
}

.page-hero h1 {
    margin-bottom: 8px;
    letter-spacing: -0.04em;
}

.page-hero p {
    color: rgba(241, 245, 249, 0.92);
    font-size: 16px;
}

.section-card,
.result-card,
.export-card {
    background: #ffffff;
    border-radius: 24px;
    padding: 24px;
    box-shadow: 0 20px 40px rgba(15, 23, 42, 0.08);
    margin-bottom: 24px;
    animation: fadeInUp 0.7s ease-out;
}

.section-header,
.section-subheader {
    color: #0f172a;
}

.section-subheader {
    color: #475569;
    margin-top: 6px;
    margin-bottom: 18px;
}

.rank-badge {
    display: inline-block;
    background-color: #2563eb;
    color: white;
    padding: 8px 16px;
    border-radius: 999px;
    font-weight: 700;
    margin-right: 12px;
    letter-spacing: 0.02em;
}

.score-bar {
    height: 12px;
    background-color: #e2e8f0;
    border-radius: 999px;
    overflow: hidden;
    margin: 14px 0;
}

.score-fill {
    height: 100%;
    background: linear-gradient(90deg, #2563eb 0%, #06b6d4 100%);
    border-radius: 999px;
    transition: width 0.8s ease;
}

.skill-pill-found {
    display: inline-block;
    background-color: #ecfeff;
    color: #0f766e;
    padding: 7px 14px;
    border-radius: 999px;
    font-size: 12px;
    margin-right: 6px;
    margin-bottom: 6px;
    font-weight: 600;
}

.skill-pill-missing {
    display: inline-block;
    background-color: #fef2f2;
    color: #991b1b;
    padding: 7px 14px;
    border-radius: 999px;
    font-size: 12px;
    margin-right: 6px;
    margin-bottom: 6px;
    font-weight: 600;
}

.top-candidate-highlight {
    background: linear-gradient(135deg, #2563eb 0%, #0ea5e9 100%);
    color: white;
    padding: 24px;
    border-radius: 24px;
    margin-bottom: 24px;
    box-shadow: 0 28px 55px rgba(37, 99, 235, 0.18);
    animation: pulseGlow 3.2s ease-in-out infinite;
}

.divider {
    border-bottom: 1px solid #e2e8f0;
    margin: 26px 0;
}

table {
    border-collapse: collapse;
    width: 100%;
}

table thead {
    background-color: #1e293b;
    color: #e2e8f0;
    font-weight: 700;
}

table th,
 table td {
    padding: 14px;
}

table th {
    text-align: left;
    border-bottom: 1px solid #cbd5e1;
}

table td {
    border-bottom: 1px solid #e2e8f0;
}

table tbody tr:hover {
    background-color: #eff6ff;
}

button[kind="primary"] {
    border-radius: 14px !important;
    background: linear-gradient(135deg, #2563eb 0%, #0ea5e9 100%) !important;
    color: #ffffff !important;
    box-shadow: 0 18px 30px rgba(37, 99, 235, 0.18) !important;
}

button {
    font-weight: 600;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

button:hover {
    transform: translateY(-1px);
}

@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(24px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes pulseGlow {
    0%, 100% {
        box-shadow: 0 0 0 0 rgba(14, 165, 233, 0.3);
    }
    50% {
        box-shadow: 0 0 30px 0 rgba(14, 165, 233, 0.1);
    }
}

.file-name-banner {
    background: #fef3c7;
    color: #92400e;
    border: 1px solid #f59e0b;
    padding: 18px 22px;
    border-radius: 18px;
    margin-bottom: 22px;
    font-size: 16px;
    font-weight: 600;
}
</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("## 🧠 AI Resume Shortlister")
    st.markdown("*Powered by NLP + TF-IDF*")
    
    st.divider()
    
    st.markdown("### 📋 How it works:")
    st.markdown("""
    1. **Input Job Description** - Paste the JD in the left panel
    2. **Select Required Skills** - Choose or let AI auto-detect
    3. **Upload Resumes** - Upload PDF/DOCX files from candidates
    4. **Run Analysis** - Click "Rank Resumes" to process all
    5. **View Results** - See rankings, scores, and download CSV
    """)
    
    st.divider()
    
    st.markdown("### 📖 About")
    st.markdown("""
    Automatically shortlist candidates using AI-powered resume analysis.
    Combines NLP skill extraction with TF-IDF document similarity.
    """)
    
    st.divider()
    
    st.caption("Built with spaCy · sklearn · Streamlit")

# Initialize session state
if "results" not in st.session_state:
    st.session_state["results"] = []

# Main content
st.markdown(
    """
    <div class='page-hero'>
        <h1>🎯 Resume Shortlisting System</h1>
        <p>Automated candidate ranking with clean analytics, skill detection, and professional matching.</p>
    </div>
    <div class='file-name-banner'>
        ⚠️ Please upload resumes with the file name set to the candidate's full name. If the system cannot reliably extract the name, the uploaded PDF/DOCX name will be used in results.
    </div>
    """,
    unsafe_allow_html=True
)

# Initialize session state for JD and skills
if "jd_text_state" not in st.session_state:
    st.session_state["jd_text_state"] = ""
if "detected_skills_state" not in st.session_state:
    st.session_state["detected_skills_state"] = []

# Two column layout for inputs
st.markdown('<div class="section-card">', unsafe_allow_html=True)
col_jd, col_upload = st.columns([3, 2])

# Left column: Job Description
with col_jd:
    st.markdown("<h3 class='section-header'>📋 Job Description</h3>", unsafe_allow_html=True)
    
    jd_text = st.text_area(
        "Paste the Job Description here:",
        value=st.session_state["jd_text_state"],
        height=220,
        placeholder="Paste your job description here... (e.g., we need a Python developer with Machine Learning expertise, SQL, Django, and AWS experience...)",
        key="jd_input"
    )
    
    # Update session state with current JD
    st.session_state["jd_text_state"] = jd_text
    
    # Auto-detect skills from JD with improved detection
    detected_skills = []
    if jd_text and len(jd_text.strip()) > 10:  # Only if JD has meaningful content
        jd_lower = jd_text.lower()
        for skill in SKILLS:
            # Better matching: check for skill with various delimiters
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, jd_lower):
                detected_skills.append(skill)
        detected_skills = sorted(detected_skills)
        st.session_state["detected_skills_state"] = detected_skills
    else:
        detected_skills = st.session_state["detected_skills_state"]
    
    # Show auto-detected count with better feedback
    if detected_skills:
        st.success(f"✅ Auto-detected {len(detected_skills)} skill(s) - Pre-selected below")
    else:
        st.info("💡 Paste your job description above to auto-detect required skills")
    
    # Store selected skills in session state for persistence
    if "selected_skills" not in st.session_state:
        st.session_state["selected_skills"] = []
    
    # If detected skills changed, update session state
    if detected_skills and st.session_state["detected_skills_state"] != detected_skills:
        st.session_state["selected_skills"] = detected_skills
    
    # Multiselect with auto-detected skills pre-selected
    # Use unique key based on detected skills to force re-render when skills change
    skills_key = f"skills_select_{len(detected_skills)}_{hash(tuple(detected_skills))}"
    required_skills = st.multiselect(
        "Required Skills (these are pre-selected from your JD):",
        options=sorted(SKILLS),
        default=detected_skills if detected_skills else [],
        key=skills_key
    )

# Right column: File Upload
with col_upload:
    st.markdown("<h3 class='section-header'>📁 Upload Resumes</h3>", unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader(
        "Choose PDF or DOCX files:",
        type=["pdf", "docx"],
        accept_multiple_files=True,
        key="file_uploader"
    )
    
    st.metric("📄 Files Uploaded", len(uploaded_files))
    
    st.info("✅ Supports: PDF, DOCX formats\n💾 Max file size: 200MB")

st.markdown('</div>', unsafe_allow_html=True)

# Center button
st.markdown("---")
col_button = st.columns([1, 1, 1])
with col_button[1]:
    process_button = st.button(
        "🚀 Rank Resumes",
        use_container_width=True,
        type="primary",
        key="process_btn"
    )

# Processing logic
if process_button:
    # Validation
    if not jd_text.strip():
        st.error("❌ Please enter a Job Description")
    elif not uploaded_files:
        st.error("❌ Please upload at least one resume")
    elif not required_skills:
        st.error("❌ Please select at least one required skill")
    else:
        results = []
        
        # Process each resume
        progress_bar = st.progress(0)
        status_placeholder = st.empty()
        
        for idx, uploaded_file in enumerate(uploaded_files):
            # Update progress
            progress = (idx + 1) / len(uploaded_files)
            progress_bar.progress(progress)
            status_placeholder.write(f"📄 Analyzing: {uploaded_file.name} ({idx + 1}/{len(uploaded_files)})")
            
            # Parse resume
            resume_text = parse_resume(uploaded_file)
            
            if not resume_text.strip():
                st.warning(f"⚠️ Could not extract text from {uploaded_file.name}")
                continue
            
            # Analyze resume
            analysis = analyze_resume(resume_text, required_skills)
            
            # Calculate scores
            tfidf_score = compute_tfidf_score(jd_text, resume_text)
            final_score = compute_final_score(
                tfidf_score,
                analysis["skill_match_pct"],
                analysis["experience_years"]
            )
            
            # Build result
            candidate_name = analysis["name"]
            inferred_name = uploaded_file.name.rsplit('.', 1)[0]
            inferred_name = re.sub(r'[-_]+', ' ', inferred_name).strip()
            inferred_name = re.sub(r'(?i)\b(resume|cv|curriculum vitae)\b', '', inferred_name).strip()
            inferred_name = inferred_name.title()

            invalid_name = (
                candidate_name == "Unknown"
                or len(candidate_name.split()) < 2
                or re.search(r'(?i)\b(hibernate|spring|docker|kubernetes|react|tamil|nadu|india|resume|cv|curriculum vitae|developer|engineer|manager|consultant|intern|company|organization|profile|summary)\b', candidate_name)
            )
            if invalid_name and inferred_name:
                candidate_name = inferred_name

            result = {
                "filename": uploaded_file.name,
                "name": candidate_name,
                "education": analysis["education"],
                "experience_years": analysis["experience_years"],
                "skills_found": analysis["skills_found"],
                "skills_missing": analysis["skills_missing"],
                "skill_match_pct": analysis["skill_match_pct"],
                "tfidf_score": tfidf_score,
                "final_score": final_score
            }
            results.append(result)
        
        # Rank candidates
        ranked_results = rank_candidates(results)
        
        # Store in session state
        st.session_state["results"] = ranked_results
        
        # Clear progress indicators
        progress_bar.empty()
        status_placeholder.empty()
        
        st.success(f"✅ Successfully analyzed {len(ranked_results)} resume(s)")

# Display results if available
if st.session_state["results"]:
    results = st.session_state["results"]
    
    st.markdown("---")
    st.markdown("<h2 class='section-header'>📊 Analysis Results</h2>", unsafe_allow_html=True)
    st.markdown("<p class='section-subheader'>Review the candidate ranking, score distribution, and export options below.</p>", unsafe_allow_html=True)
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("👥 Total Candidates", len(results))
    with col2:
        avg_score = sum(r["final_score"] for r in results) / len(results) * 100
        st.metric("📈 Avg Match Score", f"{avg_score:.1f}%")
    with col3:
        if results:
            top_name = results[0]["name"]
            top_score = results[0]["final_score"] * 100
            st.metric("🏆 Top Candidate", f"{top_name} ({top_score:.1f}%)")
    
    # Tabs for results
    tab1, tab2 = st.tabs(["📊 Rankings", "📈 Score Chart"])
    
    with tab1:
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.markdown("<h3 class='section-header'>Candidate Rankings</h3>", unsafe_allow_html=True)
        
        for idx, candidate in enumerate(results):
            with st.container():
                st.markdown('<div class="candidate-card">', unsafe_allow_html=True)
                # Rank badge and name
                rank_html = f'<span class="rank-badge">#{candidate["rank"]}</span>'
                score_pct = candidate["final_score"] * 100
                
                st.markdown(f"""
                {rank_html} **{candidate['name']}** — **{score_pct:.1f}%**
                """, unsafe_allow_html=True)
                
                # Education and experience
                col_edu, col_exp = st.columns(2)
                with col_edu:
                    st.caption(f"🎓 Education: {candidate['education']}")
                with col_exp:
                    st.caption(f"💼 Experience: {candidate['experience_years']:.1f} years")
                
                # Score bar
                score_fill_width = int(score_pct)
                st.markdown(f"""
                <div class="score-bar">
                    <div class="score-fill" style="width: {score_fill_width}%;"></div>
                </div>
                """, unsafe_allow_html=True)
                
                # Skills found and missing
                col_found, col_missing = st.columns(2)
                
                with col_found:
                    st.caption("✅ Skills Found:")
                    skills_found = candidate["skills_found"][:8]
                    skills_html = " ".join([f'<span class="skill-pill-found">{s}</span>' for s in skills_found])
                    if len(candidate["skills_found"]) > 8:
                        skills_html += f' <span class="skill-pill-found">+{len(candidate["skills_found"]) - 8} more</span>'
                    st.markdown(skills_html, unsafe_allow_html=True)
                
                with col_missing:
                    st.caption("❌ Skills Missing:")
                    skills_missing = candidate["skills_missing"][:8]
                    skills_html = " ".join([f'<span class="skill-pill-missing">{s}</span>' for s in skills_missing])
                    if len(candidate["skills_missing"]) > 8:
                        skills_html += f' <span class="skill-pill-missing">+{len(candidate["skills_missing"]) - 8} more</span>'
                    st.markdown(skills_html, unsafe_allow_html=True)
                
                st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown("### Score Distribution Chart")
        
        # Bar chart
        names = [r["name"] for r in results]
        scores = [r["final_score"] * 100 for r in results]
        
        fig = go.Figure(data=[
            go.Bar(
                x=names,
                y=scores,
                marker=dict(
                    color=scores,
                    colorscale='RdYlGn',
                    showscale=True,
                    colorbar=dict(title="Score %")
                ),
                text=[f'{s:.1f}%' for s in scores],
                textposition='outside'
            )
        ])
        
        fig.update_layout(
            title="Final Scores by Candidate",
            xaxis_title="Candidate Name",
            yaxis_title="Final Score (%)",
            height=400,
            showlegend=False,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Results table
        st.markdown("<h3 class='section-header'>Detailed Results Table</h3>", unsafe_allow_html=True)
        
        df_results = pd.DataFrame([
            {
                "Rank": r["rank"],
                "Name": r["name"],
                "Score %": f"{r['final_score'] * 100:.1f}",
                "Education": r["education"],
                "Experience": f"{r['experience_years']:.1f}y",
                "Skills Found": len(r["skills_found"])
            }
            for r in results
        ])
        
        st.dataframe(df_results, use_container_width=True, hide_index=True)
    
    # Download section
    st.markdown("---")
    st.markdown('<div class="export-card">', unsafe_allow_html=True)
    st.markdown("<h3 class='section-header'>📥 Export Results</h3>", unsafe_allow_html=True)
    
    # Prepare CSV data
    csv_data = []
    for r in results:
        csv_data.append({
            "Rank": r["rank"],
            "Name": r["name"],
            "Final Score": f"{r['final_score']:.4f}",
            "Score %": f"{r['final_score'] * 100:.1f}",
            "Education": r["education"],
            "Experience (Years)": r["experience_years"],
            "TF-IDF Score": f"{r['tfidf_score']:.4f}",
            "Skill Match %": f"{r['skill_match_pct'] * 100:.1f}",
            "Skills Found": ", ".join(r["skills_found"]),
            "Skills Missing": ", ".join(r["skills_missing"])
        })
    
    df_export = pd.DataFrame(csv_data)
    csv_bytes = df_export.to_csv(index=False).encode('utf-8')
    
    st.download_button(
        label="📥 Download as CSV",
        data=csv_bytes,
        file_name="shortlisted_candidates.csv",
        mime="text/csv",
        use_container_width=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.caption("🚀 AI Resume Shortlister v1.0 | Built with Streamlit, spaCy, and scikit-learn")
