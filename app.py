import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from fpdf import FPDF
import io

# --- 1. CORE LOGIC (Der Eddy-Grader) ---
def grade_website(url):
    if not url or pd.isna(url):
        return None, None, None
    try:
        if not url.startswith('http'):
            url = 'https://' + url
        
        start_time = time.time()
        response = requests.get(url, timeout=8, headers={'User-Agent': 'Mozilla/5.0'})
        ttfb = time.time() - start_time
        soup = BeautifulSoup(response.text, 'html.parser')
        
        score = 100
        issues = []
        
        if ttfb > 1.2:
            score -= 30
            issues.append(f"Performance-Leck: {round(ttfb, 2)}s Ladezeit. User springen ab.")
        if not soup.find('h1'):
            score -= 20
            issues.append("SEO-Fehler: Keine H1-Überschrift gefunden.")
        if not soup.find('meta', attrs={'name': 'description'}):
            score -= 15
            issues.append("Conversion-Killer: Meta-Description fehlt.")
        imgs = soup.find_all('img')
        missing_alt = [img for img in imgs if not img.get('alt')]
        if len(missing_alt) > 2:
            score -= 10
            issues.append(f"Struktur-Fehler: {len(missing_alt)} Bilder ohne Alt-Tags.")
            
        return score, issues, round(ttfb, 2)
    except Exception as e:
        return None, [f"Fehler: {str(e)}"], None

# --- 2. PDF GENERATOR ---
def create_pdf_report(url, score, issues):
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", 'B', 20)
    pdf.set_text_color(0, 255, 65) # Eddy-Grün
    pdf.cell(200, 20, txt="AGENT-BOT.DE AUDIT REPORT", ln=True, align='C')
    
    # Website Info
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(200, 10, txt=f"Analyse für: {url}", ln=True)
    pdf.ln(5)
    
    # Score
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=f"Gesamt-Score: {score}/100", ln=True)
    pdf.ln(10)
    
    # Issues
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Gefundene Schwachstellen:", ln=True)
    pdf.set_font("Arial", size=11)
    for issue in issues:
        pdf.multi_cell(0, 10, txt=f"- {issue}")
    
    pdf.ln(15)
    pdf.set_font("Arial", 'I', 10)
    pdf.multi_cell(0, 10, txt="Hinweis: Diese Fehler kosten Sie täglich potenzielle Kundenanfragen. Kontaktieren Sie uns für ein technisches Fix-Setup.")
    
    # PDF als Byte-Stream zurückgeben
    return pdf.output()

# --- 3. UI CONFIG & STYLING ---
st.set_page_config(page_title="Agent-Bot.de", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stButton>button { background-color: #00ff41; color: black; font-weight: bold; width: 100%; }
    h1, h2, h3 { color: #00ff41 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. MAIN UI ---
st.title("🤖 Agent-Bot Lead-Generator")
st.write("Verschaffe dir den unfairen Vorteil. Analysiere deine Konkurrenz oder Kunden.")

tab1, tab2 = st.tabs(["🎯 Einzel-Audit", "🔥 Bulk-Check"])

with tab1:
    url_input = st.text_input("Website URL eingeben:", placeholder="z.B. https://koeln-handwerk.de")
    if st.button("Audit starten"):
        if url_input:
            with st.spinner('Scanne Infrastruktur...'):
                score, issues, ttfb = grade_website(url_input)
                if score is not None:
                    st.divider()
                    col1, col2 = st.columns(2)
                    col1.metric("Score", f"{score}/100")
                    col2.metric("Speed", f"{ttfb}s")
                    
                    st.write("### Analyse:")
                    for issue in issues:
                        st.write(issue)
                    
                    # PDF Download Button
                    pdf_bytes = create_pdf_report(url_input, score, issues)
                    st.download_button(
                        label="📥 Audit-Report als PDF speichern",
                        data=pdf_bytes,
                        file_name=f"audit_{url_input.replace('https://','').replace('http://','')}.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.error("Konnte Seite nicht erreichen.")

with tab2:
    st.write("Lade deine CSV hoch (Spalte 'Website' erforderlich).")
    uploaded_file = st.file_uploader("Leads hochladen", type="csv")
    if uploaded_file and st.button("Liste grillen"):
        df = pd.read_csv(uploaded_file)
        results = []
        bar = st.progress(0)
        for i, row in df.iterrows():
            s, _, _ = grade_website(row['Website'])
            results.append(s if s is not None else 0)
            bar.progress((i + 1) / len(df))
        df['Score'] = results
        st.dataframe(df.sort_values(by='Score'))

st.divider()
st.caption("Agent-Bot.de | Chief of Staff Dashboard")
