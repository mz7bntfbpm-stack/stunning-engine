import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import io

# --- 1. CORE LOGIC ---
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
            issues.append(f"Performance: {round(ttfb, 2)}s Ladezeit.")
        if not soup.find('h1'):
            score -= 20
            issues.append("SEO: Keine H1-Überschrift gefunden.")
        if not soup.find('meta', attrs={'name': 'description'}):
            score -= 15
            issues.append("Marketing: Meta-Description fehlt.")
            
        return score, issues, round(ttfb, 2)
    except Exception as e:
        return None, [f"Fehler: {str(e)}"], None

# --- 2. PDF GENERATOR (Korrekt für fpdf2 2.8.5) ---
def create_pdf_report(url, score, issues):
    # 'P' = Portrait, 'mm' = Millimeter, 'A4' = Format
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    # Nutze 'helvetica' (Standard-Font ohne Deprecation)
    pdf.set_font("helvetica", 'B', 20)
    pdf.set_text_color(0, 255, 65) # Eddy-Grün
    
    # epw = Effective Page Width (berücksichtigt Ränder automatisch)
    pdf.cell(w=pdf.epw, h=20, text="AGENT-BOT.DE AUDIT REPORT", 
             new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    
    pdf.set_font("helvetica", 'B', 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(w=pdf.epw, h=10, text=f"Analyse fuer: {url}", 
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)
    
    pdf.set_font("helvetica", 'B', 16)
    pdf.cell(w=pdf.epw, h=10, text=f"Gesamt-Score: {score}/100", 
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(10)
    
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(w=pdf.epw, h=10, text="Gefundene Schwachstellen:", 
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font("helvetica", size=11)
    for issue in issues:
        # Ersetze Umlaute für Standard-PDF-Fonts oder nutze multi_cell
        safe_issue = issue.replace('ü','ue').replace('ä','ae').replace('ö','oe').replace('ß','ss')
        pdf.multi_cell(w=pdf.epw, h=8, text=f"- {safe_issue}", 
                       new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.ln(15)
    pdf.set_font("helvetica", 'I', 10)
    msg = "Hinweis: Diese Fehler kosten Sie taeglich Leads. Kontaktieren Sie uns fuer ein Fix-Setup."
    pdf.multi_cell(w=pdf.epw, h=8, text=msg)
    
    return pdf.output()

# --- 3. UI ---
st.set_page_config(page_title="Agent-Bot.de", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stButton>button { background-color: #00ff41; color: black; font-weight: bold; width: 100%; }
    h1, h2, h3 { color: #00ff41 !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 Agent-Bot Lead-Generator")

tab1, tab2 = st.tabs(["🎯 Einzel-Audit", "🔥 Bulk-Check"])

with tab1:
    url_input = st.text_input("Website URL eingeben:", placeholder="z.B. https://koeln-handwerk.de")
    if st.button("Audit starten"):
        if url_input:
            with st.spinner('Scanne...'):
                score, issues, ttfb = grade_website(url_input)
                if score is not None:
                    st.divider()
                    st.metric("Score", f"{score}/100")
                    
                    st.write("### Analyse:")
                    for issue in issues:
                        st.write(issue)
                    
                    # PDF Erstellung
                    try:
                        pdf_output = create_pdf_report(url_input, score, issues)
                        st.download_button(
                            label="📥 Audit-Report als PDF speichern",
                            data=bytes(pdf_output),
                            file_name="audit_report.pdf",
                            mime="application/pdf"
                        )
                    except Exception as e:
                        st.error(f"PDF-Fehler: {str(e)}")

with tab2:
    st.write("Lade deine CSV hoch (Spalte 'Website' erforderlich).")
    uploaded_file = st.file_uploader("Leads hochladen", type="csv")
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        if 'Website' in df.columns:
            if st.button("Liste grillen"):
                results = []
                bar = st.progress(0)
                for i, row in df.iterrows():
                    s, _, _ = grade_website(row['Website'])
                    results.append(s if s is not None else 0)
                    bar.progress((i + 1) / len(df))
                df['Score'] = results
                st.dataframe(df.sort_values(by='Score'))
        else:
            st.error("Spalte 'Website' fehlt in der CSV!")
