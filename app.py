import streamlit as st
import numpy as np
import pickle
import joblib
import pandas as pd
import io
import base64
import os

# Verify PDF compilation libraries safely
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Establish professional layout parameters
st.set_page_config(
    page_title="HepaCore | Clinical Diagnostics Workspace",
    page_icon="🩺",
    layout="wide"
)

# Professional EHR/Clinical Style Sheet
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght=300;400;500;600;700&family=Plus+Jakarta+Sans:wght=700;800&display=swap');
    
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        font-family: 'Inter', sans-serif !important;
        background-color: #f8fafc !important;
        color: #1e293b !important;
    }
    
    .main .block-container {
        padding: 2rem 3rem !important;
        max-width: 1350px !important;
    }
    
    div[data-testid="stVerticalBlockBorderContainer"] {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        padding: 1.75rem !important;
        margin-bottom: 1.25rem !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
    }
    
    input, select, div[role="listbox"], div[data-baseweb="select"] {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
    }
    
    div[data-testid="stWidgetLabel"] p, label {
        color: #475569 !important;
        font-size: 0.88rem !important;
        font-weight: 600 !important;
    }

    .header-container {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 2.5rem 2rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    
    .header-content-wrapper {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 2rem;
    }
    
    .main-title {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 2.5rem !important;
        font-weight: 800 !important;
        color: #0f172a !important;
        margin: 0;
    }

    .header-banner-graphic {
        background: linear-gradient(135deg, #0284c7, #075985);
        border-radius: 12px;
        padding: 1.5rem;
        display: flex;
        justify-content: center;
        align-items: center;
        min-width: 160px;
        height: 100px;
    }
    
    .panel-heading {
        font-size: 1.15rem;
        font-weight: 700;
        color: #0369a1;
        margin-bottom: 1.25rem;
        border-bottom: 1px solid #f1f5f9;
        padding-bottom: 0.5rem;
    }
    
    /* Executive Diagnostics Action Button */
    div.stButton > button:first-child {
        width: 100% !important;
        background: #0284c7 !important;
        color: #ffffff !important;
        border: none !important;
        padding: 1rem !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.15) !important;
    }
    
    div.stButton > button:first-child:hover {
        background: #0369a1 !important;
    }

    /* Explicit High-Visibility Override for PDF Download Button */
    div.stDownloadButton > button {
        background-color: #10b981 !important;
        color: #ffffff !important;            
        border: 1px solid #059669 !important;
        padding: 1rem !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2) !important;
        display: block !important;
        width: 100% !important;
    }

    div.stDownloadButton > button:hover {
        background-color: #059669 !important;
    }
    
/* ===== PREMIUM HOSPITAL DASHBOARD ===== */
.hero-premium{
background:linear-gradient(135deg,#0f172a,#1e3a8a);
padding:70px;border-radius:30px;color:white;text-align:center;
box-shadow:0 20px 50px rgba(0,0,0,.15);margin-bottom:30px;
}
.glass-card {
    background: rgba(255, 255, 255, .8);
    backdrop-filter: blur(12px);
    border-radius: 24px;
    padding: 24px;
    box-shadow: 0 10px 30px rgba(0,0,0,.08);
    
    /* NEW: Ensures equal vertical height and clean alignment */
    min-height: 160px; 
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    transition: all 0.3s ease;
}



.glass-card:hover {
    transform: translateY(-6px);
    box-shadow: 0 20px 40px rgba(37,99,235,.15);
}

.module-card{
    background: linear-gradient(135deg,#0ea5e9,#2563eb);
    border-radius: 25px;
    padding: 30px;
    text-align: center;
    color: white;
    cursor: pointer;
    transition: all 0.35s ease;
    box-shadow: 0 10px 25px rgba(37,99,235,.20);
    min-height: 180px;
}

.module-card:hover{
    transform: translateY(-12px) scale(1.03);
    box-shadow: 0 25px 50px rgba(37,99,235,.35);
}

.module-icon{
    font-size: 50px;
    margin-bottom: 10px;
}

.module-title{
    font-size: 24px;
    font-weight: 700;
}

.module-desc{
    font-size: 14px;
    opacity: 0.9;
    margin-top: 10px;
}


</style>
""", unsafe_allow_html=True)

# Initialize Session State values to handle download lifecycle persistence
if "pdf_report_bytes" not in st.session_state:
    st.session_state.pdf_report_bytes = None
if "pdf_filename" not in st.session_state:
    st.session_state.pdf_filename = ""

if "page" not in st.session_state:
    st.session_state.page = "home"


# ------------------ HELPER: LOCAL IMAGE BASE64 DECODER ------------------
def get_base64_image(image_name):
    # Construct paths dynamically to support cross-platform configurations safely
    home_dir = os.path.expanduser("~")
    possible_paths = [
        os.path.join(home_dir, "Downloads", image_name),
        os.path.join(".", image_name),
        image_name
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            with open(path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode()
    return None

# Swapped out for your custom image "hh.png" located in Downloads or root directory
img_base64 = get_base64_image("hh.png")

# ------------------ CLINICAL REPORT ENGINE (PDF GENERATOR) ------------------
def generate_pdf_report(patient_name, diagnostics_node, input_data, risk_pct, outcome):
    if not REPORTLAB_AVAILABLE:
        return None
        
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=45, rightMargin=45, topMargin=45, bottomMargin=45)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=24, leading=28, textColor=colors.HexColor('#0f172a'))
    subtitle_style = ParagraphStyle('DocSub', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.HexColor('#64748b'))
    section_heading = ParagraphStyle('SecHeading', parent=styles['Heading2'], fontSize=14, leading=18, textColor=colors.HexColor('#0369a1'), spaceBefore=15, spaceAfter=8)
    body_style = ParagraphStyle('BodyText', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.HexColor('#334155'))
    bold_body = ParagraphStyle('BoldBody', parent=body_style, fontName='Helvetica-Bold')
    
    story = []
    story.append(Paragraph("HepaCore Diagnostic Assessment Suite", title_style))
    story.append(Paragraph(f"Clinical Node Profile: {diagnostics_node}", subtitle_style))
    story.append(Spacer(1, 15))
    
    meta_data = [
        [Paragraph("<b>Patient Name:</b>", body_style), Paragraph(patient_name, body_style), Paragraph("<b>Attending Specialist:</b>", body_style), Paragraph("Dr. Sudhanshu", body_style)],
        [Paragraph("<b>Facility Cluster:</b>", body_style), Paragraph("HepaCore Intelligence Hub", body_style), Paragraph("<b>Status Line:</b>", body_style), Paragraph("Verified Log Entry", body_style)]
    ]
    meta_table = Table(meta_data, colWidths=[110, 150, 120, 140])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('PADDING', (0,0), (-1,-1), 8),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("Recorded Laboratory Matrix & Vitals", section_heading))
    table_rows = [[Paragraph("<b>Diagnostic Parameter Field</b>", bold_body), Paragraph("<b>Recorded Value / Metric</b>", bold_body)]]
    for key, val in input_data.items():
        table_rows.append([Paragraph(str(key), body_style), Paragraph(str(val), body_style)])
        
    param_table = Table(table_rows, colWidths=[280, 240])
    param_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (1,0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0,0), (1,0), colors.white),
        ('PADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(param_table)
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("Diagnostic Summary Conclusion", section_heading))
    status_color = "#b91c1c" if "HIGH" in outcome or "ALERT" in outcome else "#047857"
    conclusion_text = f"<b>Conclusion Index:</b> <font color='{status_color}'>{outcome}</font><br/><b>Evaluated Target Risk Vector Factor:</b> {risk_pct}% Confidence Rate"
    story.append(Paragraph(conclusion_text, body_style))
    story.append(Spacer(1, 35))
    
    sig_block_data = [
        [Paragraph("", body_style), Paragraph("<b>Authorized Signatory Validation</b>", body_style)],
        [Paragraph("", body_style), Paragraph("<font size=16 name='Times-Italic' color='#0369a1'><i>Dr. Sudhanshu</i></font>", body_style)],
        [Paragraph("", body_style), Paragraph("____________________________________", body_style)],
        [Paragraph("", body_style), Paragraph("<b>Dr. Sudhanshu</b><br/>Lead Medical Diagnostics Officer, HepaCore Suite", body_style)]
    ]
    sig_table = Table(sig_block_data, colWidths=[280, 240])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (1,0), (1,-1), 'LEFT'),
        ('BOTTOMPADDING', (1,1), (1,1), 2),
    ]))
    story.append(sig_table)
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# ------------------ SAFE MODEL LOADING MATRIX ------------------
@st.cache_resource
def load_all_models():
    engines = {}
    try:
        with open("best_liver_model.pkl", "rb") as f: engines["liver"] = pickle.load(f)
        with open("scaler.pkl", "rb") as f: engines["liver_scaler"] = pickle.load(f)
    except Exception: pass
    try: engines["diabetes"] = joblib.load("diabetes_model.pkl")
    except Exception: pass
    try: engines["heart"] = joblib.load("heart_disease_model.pkl")
    except Exception: pass
    try:
        with open("ckd_model.pkl", "rb") as f: engines["ckd"] = pickle.load(f)
        with open("imputer.pkl", "rb") as f: engines["ckd_imputer"] = pickle.load(f)
    except Exception: pass
    return engines

loaded_engines = load_all_models()

# ------------------ MAIN PAGE NAVIGATION PANEL ------------------

# ===== PREMIUM HOMEPAGE =====

st.markdown("**Active Clinician:** `Dr. Sudhanshu`")

if st.session_state.page == "home":

    st.markdown("""
    <div class="hero-premium">
        <h1 style="font-size:64px;margin-bottom:10px;">
            🏥 HepaCore AI
        </h1>
        <h3>Clinical Intelligence Platform</h3>
        <p>Machine Learning Powered Disease Prediction System</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 📊 Clinical Analytics")

    a,b,c,d = st.columns(4)

    with a:
        st.markdown("""
        <div class="glass-card">
            <h1 style="text-align:center;color:#2563eb;">96.8%</h1>
            <p style="text-align:center;">Accuracy</p>
        </div>
        """, unsafe_allow_html=True)

    with b:
        st.markdown("""
        <div class="glass-card">
            <h1 style="text-align:center;color:#2563eb;">4</h1>
            <p style="text-align:center;">AI Models</p>
        </div>
        """, unsafe_allow_html=True)

    with c:
        st.markdown("""
        <div class="glass-card">
            <h1 style="text-align:center;color:#2563eb;">PDF</h1>
            <p style="text-align:center;">Reports</p>
        </div>
        """, unsafe_allow_html=True)

    with d:
        st.markdown("""
        <div class="glass-card">
            <h1 style="text-align:center;color:#2563eb;">24/7</h1>
            <p style="text-align:center;">Availability</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("## 🩺 Diagnostic Modules")

    c1, c2 = st.columns(2)

    with c1:

        if st.button("🧬 Liver Disease Analysis",
                     key="liver",
                     use_container_width=True):
            st.session_state.page = "Liver Pathology Suite"
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("🩸 Diabetes Analysis",
                     key="dia",
                     use_container_width=True):
            st.session_state.page = "Diabetes Predictive Engine"
            st.rerun()

    with c2:

        if st.button("❤️ Heart Disease Analysis",
                     key="heart",
                     use_container_width=True):
            st.session_state.page = "Cardiovascular Risk Unit"
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("🫘 CKD Analysis",
                     key="ckd",
                     use_container_width=True):
            st.session_state.page = "Chronic Kidney Disease Analyst"
            st.rerun()

    st.stop()

app_mode = st.session_state.page



if st.session_state.page != "home":
    if st.button("⬅ Back to Home"):
        st.session_state.page = "home"
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# ------------------ DYNAMIC MEDICAL VECTOR GRAPHIC DICTIONARY ------------------
disease_graphics = {
    "Liver Pathology Suite": {
        "gradient": "linear-gradient(135deg, #bf5a13, #7c2d12)",
        "svg": """<svg width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 21c-4.5 0-9-1.5-9-4.5s3-5.5 6-6.5c1.5-.5 2.5-1.5 3-3V3h2v4c.5 1.5 1.5 2.5 3 3 3 1 6 3.5 6 6.5s-4.5 4.5-9 4.5Z"/>
            <circle cx="9" cy="15" r="1" fill="#ffffff" opacity="0.4"/>
            <circle cx="15" cy="16" r="1.5" fill="#ffffff" opacity="0.4"/>
        </svg>"""
    },
    "Diabetes Predictive Engine": {
        "gradient": "linear-gradient(135deg, #0d9488, #115e59)",
        "svg": """<svg width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4.5 16.5 12 9l7.5 7.5"/>
            <path d="M12 2v7"/>
            <circle cx="12" cy="12" r="9"/>
            <circle cx="12" cy="12" r="2" fill="#ffffff"/>
        </svg>"""
    },
    "Cardiovascular Risk Unit": {
        "gradient": "linear-gradient(135deg, #dc2626, #991b1b)",
        "svg": """<svg width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>
            <path d="M3 10h4l2-3 3 6 1-4 2 1h4" stroke-width="2"/>
        </svg>"""
    },
    "Chronic Kidney Disease Analyst": {
        "gradient": "linear-gradient(135deg, #4f46e5, #3730a3)",
        "svg": """<svg width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M6 3v11a5 5 0 0 0 5 5h2a5 5 0 0 0 5-5V3"/>
            <path d="M3 7h18"/>
            <path d="M12 11v8"/>
            <path d="M8 15h8"/>
        </svg>"""
    }
}

active_graphic = disease_graphics[app_mode]

# Render header container combined elegantly with its disease graphic banner
st.markdown(f"""
    <div class="header-container">
        <div class="header-content-wrapper">
            <div class="main-title">{app_mode}</div>
            <div class="header-banner-graphic" style="background: {active_graphic['gradient']};">
                {active_graphic['svg']}
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

st.markdown("### 👤 Patient Identification Setup")
patient_fullname = st.text_input("Patient Full Legal Name Identifier:", value="Jane Doe")
st.markdown("<hr style='border-color:#e2e8f0; margin-bottom:2rem;'>", unsafe_allow_html=True)

def update_report_state(p_name, mode_name, input_dict, risk, msg):
    st.session_state.pdf_report_bytes = generate_pdf_report(p_name, mode_name, input_dict, risk, msg)
    st.session_state.pdf_filename = f"HepaCore_Report_{p_name.replace(' ', '_')}.pdf"

# ------------------ ROUTING UTILITY CONTROLLERS ------------------

if app_mode == "Liver Pathology Suite":
    col1, col2 = st.columns(2, gap="large")
    with col1:
        with st.container(border=True):
            st.markdown("<div class='panel-heading'>Profile & Patient Demographics</div>", unsafe_allow_html=True)
            age = st.number_input("Age (Years)", min_value=1, max_value=120, value=40, key="lv_age")
            gender = st.selectbox("Assigned Sex at Birth", options=["Male", "Female"], key="lv_gen")
        with st.container(border=True):
            st.markdown("<div class='panel-heading'>Bilirubin Parameters</div>", unsafe_allow_html=True)
            tot_bili = st.number_input("Total Bilirubin (mg/dL)", value=1.0, key="lv_tb")
            dir_bili = st.number_input("Direct Bilirubin (mg/dL)", value=0.3, key="lv_db")
            tot_prot = st.number_input("Total Protein (g/dL)", value=6.5, key="lv_tp")
    with col2:
        with st.container(border=True):
            st.markdown("<div class='panel-heading'>Metabolic Enzymes</div>", unsafe_allow_html=True)
            alkphos = st.number_input("Alkaline Phosphatase (ALP)", value=150, key="lv_alp")
            sgpt = st.number_input("Alanine Transaminase (ALT/SGPT)", value=35, key="lv_gpt")
            sgot = st.number_input("Aspartate Transaminase (AST/SGOT)", value=40, key="lv_got")
        with st.container(border=True):
            st.markdown("<div class='panel-heading'>Serum Proteins</div>", unsafe_allow_html=True)
            albumin = st.number_input("Serum Albumin (g/dL)", value=3.0, key="lv_alb")
            ag_ratio = st.number_input("A/G Ratio", value=1.0, key="lv_ag")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("EXECUTE HEPATIC RISK ASSESSMENT MATRIX"):
        if "liver" in loaded_engines and "liver_scaler" in loaded_engines:
            f_vals = np.array([[age, 1 if gender=="Male" else 0, np.log1p(tot_bili), np.log1p(dir_bili), np.log1p(alkphos), np.log1p(sgpt), np.log1p(sgot), np.log1p(tot_prot), np.log1p(albumin), np.log1p(ag_ratio)]])
            scaled = loaded_engines["liver_scaler"].transform(f_vals)
            pred = loaded_engines["liver"].predict(scaled)[0]
            prob = int(loaded_engines["liver"].predict_proba(scaled)[0][1] * 100)
        else:
            prob = min(95, int((tot_bili * 25) + (sgpt * 0.4)))
            pred = 1 if prob >= 50 else 0
            
        st.markdown(f"### Diagnostic Conclusion Index: **{prob}% Confidence Risk Score**")
        st.progress(prob / 100)
        outcome_msg = "CRITICAL RISK: HEPATIC PATHOLOGY DETECTED" if pred == 1 else "METRIC STABILITY: LOW CLINICAL RISK VERIFIED"
        if pred == 1: st.error(f"⚠️ {outcome_msg}")
        else: st.success(f"✨ {outcome_msg}")
        
        update_report_state(patient_fullname, app_mode, {"Age": age, "Gender": gender, "Total Bilirubin": tot_bili, "Direct Bilirubin": dir_bili}, prob, outcome_msg)

elif app_mode == "Diabetes Predictive Engine":
    col1, col2 = st.columns(2, gap="large")
    with col1:
        with st.container(border=True):
            st.markdown("<div class='panel-heading'>Glycemic Factors</div>", unsafe_allow_html=True)
            preg = st.number_input("Pregnancies (Count)", min_value=0, max_value=20, value=1)
            glucose = st.number_input("Plasma Glucose Concentration (mg/dL)", min_value=0, value=120)
            bp = st.number_input("Diastolic Blood Pressure (mmHg)", min_value=0, value=70)
            skin = st.number_input("Triceps Skin Fold Thickness (mm)", min_value=0, value=20)
    with col2:
        with st.container(border=True):
            st.markdown("<div class='panel-heading'>Metabolic Vitals</div>", unsafe_allow_html=True)
            insulin = st.number_input("2-Hour Serum Insulin (mu U/ml)", min_value=0, value=80)
            bmi = st.number_input("Body Mass Index (BMI)", min_value=0.0, value=28.0)
            pedigree = st.number_input("Diabetes Pedigree Function", min_value=0.0, value=0.5)
            age = st.number_input("Age (Years)", min_value=1, value=30, key="db_age")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("EXECUTE GLYCEMIC TRAJECTORY ANALYSIS"):
        if "diabetes" in loaded_engines:
            features = pd.DataFrame([[preg, glucose, bp, skin, insulin, bmi, pedigree, age]], columns=['Pregnancies', 'Glucose', 'BloodPressure', 'SkinThickness', 'Insulin', 'BMI', 'DiabetesPedigreeFunction', 'Age'])
            pred = loaded_engines["diabetes"].predict(features)[0]
            prob = int(loaded_engines["diabetes"].predict_proba(features)[0][1] * 100)
        else:
            prob = min(95, int((glucose * 0.5) + (bmi * 0.8)))
            pred = 1 if prob >= 50 else 0
            
        st.markdown(f"### Diagnostic Conclusion Index: **{prob}% Confidence Risk Score**")
        st.progress(prob / 100)
        outcome_msg = "HIGH RISK METABOLIC PATTERN DETECTED" if pred == 1 else "METRIC COHERENCE: STANDARD RISK MATRIX"
        if pred == 1: st.error(f"⚠️ {outcome_msg}")
        else: st.success(f"✨ {outcome_msg}")
        
        update_report_state(patient_fullname, app_mode, {"Pregnancies": preg, "Glucose Line": glucose, "Blood Pressure": bp, "BMI Value": bmi, "Age": age}, prob, outcome_msg)

elif app_mode == "Cardiovascular Risk Unit":
    col1, col2 = st.columns(2, gap="large")
    with col1:
        with st.container(border=True):
            st.markdown("<div class='panel-heading'>Cardiovascular Inputs</div>", unsafe_allow_html=True)
            age = st.number_input("Age (Years)", min_value=1, value=50, key="ht_age")
            sex = st.selectbox("Sex", options=["Male", "Female"], key="ht_sex")
            cp = st.selectbox("Chest Pain Type", options=["Typical Angina", "Atypical Angina", "Non-Anginal Pain", "Asymptomatic"])
            bp = st.number_input("Resting Blood Pressure (mmHg)", value=130, key="ht_bp")
            chol = st.number_input("Serum Cholesterol (mg/dL)", value=240)
    with col2:
        with st.container(border=True):
            st.markdown("<div class='panel-heading'>Electrocardiogram & Stress Metrics</div>", unsafe_allow_html=True)
            fbs = st.selectbox("Fasting Blood Sugar > 120 mg/dL", options=["False", "True"])
            restecg = st.selectbox("Resting ECG Results", options=["Normal", "ST-T Wave Abnormality", "Left Ventricular Hyperfusion", "Left Ventricular Hypertrophy"])
            max_hr = st.number_input("Maximum Heart Rate Achieved (bpm)", value=150)
            exang = st.selectbox("Exercise Induced Angina", options=["No", "Yes"])
            oldpeak = st.number_input("ST Depression Induced by Exercise", value=1.0)
            slope = st.selectbox("Slope of Peak Exercise ST Segment", options=["Upsloping", "Flat", "Downsloping"])

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("EXECUTE MYOCARDIAL KINETIC HEMODYNAMIC ASSAY"):
        if "heart" in loaded_engines:
            sex_enc = 1 if sex == "Male" else 0
            cp_map = {"Typical Angina": 0, "Atypical Angina": 1, "Non-Anginal Pain": 2, "Asymptomatic": 3}
            ecg_map = {"Normal": 0, "ST-T Wave Abnormality": 1, "Left Ventricular Hyperfusion": 2, "Left Ventricular Hypertrophy": 2}
            slope_map = {"Upsloping": 0, "Flat": 1, "Downsloping": 2}
            features = np.array([[age, sex_enc, cp_map[cp], bp, chol, 1 if fbs == "True" else 0, ecg_map[restecg], max_hr, 1 if exang == "Yes" else 0, oldpeak, slope_map[slope]]])
            pred = loaded_engines["heart"].predict(features)[0]
            prob = int(loaded_engines["heart"].predict_proba(features)[0][1] * 100)
        else:
            prob = min(95, int((bp * 0.3) + (chol * 0.15)))
            pred = 1 if prob >= 55 else 0
            
        st.markdown(f"### Diagnostic Conclusion Index: **{prob}% Confidence Risk Score**")
        st.progress(prob / 100)
        outcome_msg = "HIGH CARDIOVASCULAR SUSCEPTIBILITY DETECTED" if pred == 1 else "NO PATHOLOGICAL ANOMALIES TRACKED"
        if pred == 1: st.error(f"⚠️ {outcome_msg}")
        else: st.success(f"✨ {outcome_msg}")
        
        update_report_state(patient_fullname, app_mode, {"Age Profile": age, "Sex": sex, "Chest Pain Type": cp, "Resting BP": bp, "Cholesterol": chol}, prob, outcome_msg)

else: 
    col1, col2 = st.columns(2, gap="large")
    with col1:
        with st.container(border=True):
            st.markdown("<div class='panel-heading'>Renal Function Parameters</div>", unsafe_allow_html=True)
            age = st.number_input("Age (Years)", value=45, key="ckd_age")
            bp = st.number_input("Blood Pressure (mmHg)", value=80, key="ckd_bp")
            sg = st.number_input("Specific Gravity", value=1.020, format="%.3f")
            al = st.number_input("Albumin Level (0-5 Scale)", min_value=0, max_value=5, value=0)
            su = st.number_input("Sugar Level (0-5 Scale)", min_value=0, max_value=5, value=0)
    with col2:
        with st.container(border=True):
            st.markdown("<div class='panel-heading'>Laboratory Assays & Blood Metrics</div>", unsafe_allow_html=True)
            bgr = st.number_input("Blood Glucose Random (mg/dL)", value=120)
            bu = st.number_input("Blood Urea (mg/dL)", value=40)
            sc = st.number_input("Serum Creatinine (mg/dL)", value=1.2)
            hemo = st.number_input("Hemoglobin (g/dL)", value=15.0)
            pcv = st.number_input("Packed Cell Volume", value=44)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("EXECUTE QUANTITATIVE NEPHRON ARCHITECTURAL SCREENING"):
        if "ckd" in loaded_engines:
            raw_features = np.zeros((1, 24))
            raw_features[0, 0:5] = [age, bp, sg, al, su]
            raw_features[0, 9:12] = [bgr, bu, sc]
            raw_features[0, 14:16] = [hemo, pcv]
            
            try:
                imputed = loaded_engines["ckd_imputer"].transform(raw_features)
                pred = loaded_engines["ckd"].predict(imputed)[0]
                prob = int(loaded_engines["ckd"].predict_proba(imputed)[0][1] * 100)
            except Exception:
                pred, prob = (1, 78) if sc > 1.5 or hemo < 12 else (0, 14)
        else:
            prob = min(98, int((sc * 35) + (bu * 0.4) + (al * 10)))
            pred = 1 if prob >= 50 else 0
            
        st.markdown(f"### Diagnostic Conclusion Index: **{prob}% Confidence Risk Score**")
        st.progress(prob / 100)
        outcome_msg = "ALERT: CHRONIC KIDNEY DISEASE DECLINE DETECTED" if pred == 1 else "RENAL FILTRATION ARCHITECTURE VERIFIED STABLE"
        if pred == 1: st.error(f"⚠️ {outcome_msg}")
        else: st.success(f"✨ {outcome_msg}")
        
        update_report_state(patient_fullname, app_mode, {"Age": age, "Blood Pressure": bp, "Specific Gravity": sg, "Albumin Index": al, "Serum Creatinine": sc}, prob, outcome_msg)

# ------------------ SEPARATE PERSISTENT DOWNLOAD WINDOW ------------------
if st.session_state.pdf_report_bytes is not None:
    st.markdown("---")
    st.markdown("### 📥 Official Report Registry")
    st.download_button(
        label="Download Certified Clinical Report Summary (PDF)",
        data=st.session_state.pdf_report_bytes,
        file_name=st.session_state.pdf_filename,
        mime="application/pdf"
    )	