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

[data-testid="stSidebar"] {
    background-color: #0f172a;
}

[data-testid="stSidebar"] .stMarkdown {
    color: white;
}

[data-testid="stSidebar"] h1, 
[data-testid="stSidebar"] h2, 
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4,
[data-testid="stSidebar"] h5,
[data-testid="stSidebar"] p {
    color: white;
}

.metric-card {
    background-color: #f8fafc;
    padding: 20px;
    border-radius: 12px;
    border-left: 4px solid #10b981;
}

.candidate-card {
    background-color: #f8fafc;
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 15px;
    border-left: 5px solid #10b981;
}

.rank-badge {
    display: inline-block;
    background-color: #10b981;
    color: white;
    padding: 5px 12px;
    border-radius: 20px;
    font-weight: 600;
    margin-right: 10px;
}

.score-bar {
    height: 8px;
    background-color: #e5e7eb;
    border-radius: 4px;
    overflow: hidden;
    margin: 10px 0;
}

.score-fill {
    height: 100%;
    background: linear-gradient(90deg, #ef4444, #f59e0b, #10b981);
    border-radius: 4px;
}

.skill-pill-found {
    display: inline-block;
    background-color: #d1fae5;
    color: #065f46;
    padding: 4px 10px;
    border-radius: 16px;
    font-size: 12px;
    margin-right: 5px;
    margin-bottom: 5px;
    font-weight: 500;
}

.skill-pill-missing {
    display: inline-block;
    background-color: #fee2e2;
    color: #991b1b;
    padding: 4px 10px;
    border-radius: 16px;
    font-size: 12px;
    margin-right: 5px;
    margin-bottom: 5px;
    font-weight: 500;
}

.top-candidate-highlight {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    color: white;
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 20px;
}

.divider {
    border-bottom: 1px solid #e5e7eb;
    margin: 20px 0;
}

table {
    border-collapse: collapse;
    width: 100%;
}

table thead {
    background-color: #1f2937;
    color: white;
    font-weight: 600;
}

table th {
    padding: 12px;
    text-align: left;
    border-bottom: 2px solid #e5e7eb;
}

table td {
    padding: 12px;
    border-bottom: 1px solid #e5e7eb;
}

table tbody tr:hover {
    background-color: #f8fafc;
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
st.markdown("# 🎯 Resume Shortlisting System")

# Initialize session state for JD and skills
if "jd_text_state" not in st.session_state:
    st.session_state["jd_text_state"] = ""
if "detected_skills_state" not in st.session_state:
    st.session_state["detected_skills_state"] = []

# Two column layout for inputs
col_jd, col_upload = st.columns([3, 2])

# Left column: Job Description
with col_jd:
    st.markdown("### 📋 Job Description")
    
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
    st.markdown("### 📁 Upload Resumes")
    
    uploaded_files = st.file_uploader(
        "Choose PDF or DOCX files:",
        type=["pdf", "docx"],
        accept_multiple_files=True,
        key="file_uploader"
    )
    
    st.metric("📄 Files Uploaded", len(uploaded_files))
    
    st.info("✅ Supports: PDF, DOCX formats\n💾 Max file size: 200MB")

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
            result = {
                "filename": uploaded_file.name,
                "name": analysis["name"],
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
    st.markdown("## 📊 Analysis Results")
    
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
        st.markdown("### Candidate Rankings")
        
        for idx, candidate in enumerate(results):
            with st.container():
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
        st.markdown("### Detailed Results Table")
        
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
    st.markdown("### 📥 Export Results")
    
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

# Footer
st.markdown("---")
st.caption("🚀 AI Resume Shortlister v1.0 | Built with Streamlit, spaCy, and scikit-learn")
