import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import io

# --- 1. CORE LOGIC (Der Eddy-Grader) ---
def grade_website(url):
    if not url or pd.isna(url):
        return None, None, None
    
    try:
        # URL bereinigen
        if not url.startswith('http'):
            url = 'https://' + url
        
        # Performance Messung
        start_time = time.time()
        response = requests.get(url, timeout=8, headers={'User-Agent': 'Mozilla/5.0'})
        ttfb = time.time() - start_time
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        score = 100
        issues = []
        
        # Check 1: Speed
        if ttfb > 1.2:
            score -= 30
            issues.append(f"🔴 Speed: {round(ttfb, 2)}s - Viel zu langsam. User springen ab.")
        
        # Check 2: SEO H1
        if not soup.find('h1'):
            score -= 20
            issues.append("🔴 H1-Tag fehlt: Google weiß nicht, was du tust.")
            
        # Check 3: Meta Description
        if not soup.find('meta', attrs={'name': 'description'}):
            score -= 15
            issues.append("🔴 Meta-Description: Dein Google-Eintrag sieht unprofessionell aus.")

        # Check 4: Images Alt-Tags
        imgs = soup.find_all('img')
        missing_alt = [img for img in imgs if not img.get('alt')]
        if len(missing_alt) > 2:
            score -= 10
            issues.append(f"🔴 Bilder: {len(missing_alt)} Bilder ohne Alt-Text (schlecht für SEO).")
            
        return score, issues, round(ttfb, 2)
    except Exception as e:
        return None, [f"Fehler: Seite nicht erreichbar ({str(e)})"], None

# --- 2. UI CONFIG & STYLING (Eddy-Vibe) ---
st.set_page_config(page_title="Agent-Bot.de | Audit", page_icon="⚡", layout="wide")

# Custom CSS für den Dark-Tech-Look
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stButton>button { background-color: #00ff41; color: black; font-weight: bold; border-radius: 5px; border: none; }
    .stProgress > div > div > div > div { background-color: #00ff41; }
    h1, h2, h3 { color: #00ff41 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR (Navigation & Status) ---
st.sidebar.title("🤖 Agent-Bot Control")
st.sidebar.write("Status: **Online**")
st.sidebar.write("Mode: **Aggressive Lead Gen**")
st.sidebar.divider()
st.sidebar.info("Hannes, hier ist dein Dashboard. Finde die schwächsten Seiten und fixxe sie.")

# --- 4. MAIN CONTENT ---
st.title("⚡ Agent-Bot Lead-Maschine")
st.subheader("Kein KI-Hype. Nur harte Daten und bessere Conversions.")

tab1, tab2 = st.tabs(["🎯 Einzel-Audit", "🔥 Bulk-Check (Hit-Liste)"])

# --- TAB 1: EINZEL-AUDIT ---
with tab1:
    st.markdown("### Teste eine spezifische URL")
    single_url = st.text_input("Website eingeben (z.B. schreiner-koeln.de)", "")
    
    if st.button("Audit starten"):
        if single_url:
            with st.spinner('Analysiere...'):
                score, issues, ttfb = grade_website(single_url)
                if score is not None:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Health Score", f"{score}/100")
                        st.progress(score / 100)
                    with col2:
                        st.metric("Reaktionszeit", f"{ttfb}s")
                    
                    st.write("### Analyse-Ergebnis:")
                    for issue in issues:
                        st.write(issue)
                    
                    if score < 60:
                        st.error("Urteil: Katastrophe. Ein gefundenes Fressen für den Outreach.")
                    else:
                        st.success("Urteil: Okay, aber Potenzial für Automatisierung.")
                else:
                    st.error("Konnte die Seite nicht scannen. Check die URL.")

# --- TAB 2: BULK-CHECK ---
with tab2:
    st.markdown("### Lade deine 'leads_koeln.csv' hoch")
    uploaded_file = st.file_uploader("CSV Datei hochladen (Spalte 'Website' muss enthalten sein)", type=["csv"])
    
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        if 'Website' in df.columns:
            if st.button("Gesamte Liste grillen"):
                st.write(f"Starte Audit für {len(df)} Firmen...")
                
                results = []
                progress_text = st.empty()
                bar = st.progress(0)
                
                for i, row in df.iterrows():
                    url = row['Website']
                    progress_text.text(f"Checke: {url}")
                    score, _, _ = grade_website(url)
                    results.append(score if score is not None else 0)
                    bar.progress((i + 1) / len(df))
                
                df['Score'] = results
                # Sortieren: Schlechteste zuerst (Target-Prio)
                df_sorted = df.sort_values(by='Score', ascending=True)
                
                st.divider()
                st.write("### 🔥 Deine Hit-Liste (Schlechteste zuerst)")
                st.dataframe(df_sorted, use_container_width=True)
                
                # Download Button für die Ergebnisse
                csv = df_sorted.to_csv(index=False).encode('utf-8')
                st.download_button("Target-Liste exportieren", csv, "targets_ready.csv", "text/csv")
        else:
            st.error("Die CSV braucht eine Spalte namens 'Website'.")
from fpdf import FPDF

def create_pdf(score, issues, url):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=f"Audit-Bericht: {url}", ln=True, align='C')
    
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Health Score: {score}/100", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Gefundene Probleme:", ln=True)
    
    pdf.set_font("Arial", size=10)
    for issue in issues:
        pdf.multi_cell(0, 10, txt=f"- {issue}")
    
    pdf.ln(10)
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(200, 10, txt="Erstellt von Agent-Bot.de", ln=True)
    
    return pdf.output(dest='S').encode('latin-1')

# Im UI (nach dem Audit):
# if score is not None:
#     pdf_data = create_pdf(score, issues, single_url)
#     st.download_button("Audit als PDF herunterladen", pdf_data, "audit_bericht.pdf", "application/pdf")

# --- 5. FOOTER ---
st.divider()
st.caption("Agent-Bot.de | Built for Performance | No AI-Fatigue allowed.")