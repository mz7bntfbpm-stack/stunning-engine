import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import pydeck as pdk
from geopy.geocoders import Nominatim
import io

# --- 1. CORE LOGIC (Audit) ---
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

# --- 2. PDF GENERATOR ---
def create_pdf_report(url, score, issues):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 20)
    pdf.set_text_color(0, 255, 65) 
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
        safe_issue = issue.replace('ü','ue').replace('ä','ae').replace('ö','oe').replace('ß','ss')
        pdf.multi_cell(w=pdf.epw, h=8, text=f"- {safe_issue}", 
                       new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    return pdf.output()

# --- 3. UI SETUP ---
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

# --- TAB 1: EINZEL-AUDIT ---
with tab1:
    url_input = st.text_input("Website URL eingeben:", placeholder="z.B. https://schreinerei-koeln.de")
    if st.button("Audit starten"):
        if url_input:
            with st.spinner('Scanne...'):
                score, issues, ttfb = grade_website(url_input)
                if score is not None:
                    st.metric("Score", f"{score}/100")
                    for issue in issues:
                        st.write(issue)
                    pdf_output = create_pdf_report(url_input, score, issues)
                    st.download_button(label="📥 PDF Report", data=bytes(pdf_output), file_name="audit.pdf", mime="application/pdf")

# --- TAB 2: BULK-CHECK & MAP ---
with tab2:
    st.write("### 🏭 Lead-Fabrik: Köln-Analyse")
    uploaded_file = st.file_uploader("Leads (CSV) hochladen", type="csv")
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        if 'Website' in df.columns:
            if st.button("🚀 Audit & Karte starten"):
                results = []
                bar = st.progress(0)
                for i, row in df.iterrows():
                    s, _, _ = grade_website(row['Website'])
                    results.append(s if s is not None else 0)
                    bar.progress((i + 1) / len(df))
                
                df['Score'] = results
                
                # Karte von Köln
                st.divider()
                st.write("### 📍 Opportunity-Map Köln")
                geolocator = Nominatim(user_agent="agent_bot_hannes")
                
                def get_coords(addr):
                    try:
                        loc = geolocator.geocode(f"{addr}, Köln")
                        return (loc.latitude, loc.longitude) if loc else (None, None)
                    except: return (None, None)

                with st.spinner('Verorte Leads...'):
                    coords = [get_coords(a) for a in df['Adresse']]
                    df['lat'] = [c[0] for c in coords]
                    df['lon'] = [c[1] for c in coords]
                    map_df = df.dropna(subset=['lat', 'lon'])
                    map_df['color'] = map_df['Score'].apply(lambda x: [255, 0, 0, 160] if x < 50 else [0, 255, 0, 160])

                    st.pydeck_chart(pdk.Deck(
                        map_style='mapbox://styles/mapbox/dark-v9',
                        initial_view_state=pdk.ViewState(latitude=50.9375, longitude=6.9603, zoom=11, pitch=45),
                        layers=[pdk.Layer('ScatterplotLayer', data=map_df, get_position='[lon, lat]', get_color='color', get_radius=180, pickable=True)],
                        tooltip={"text": "{Name}\nScore: {Score}"}
                    ))
                st.dataframe(df.sort_values(by='Score'))
        else:
            st.error("CSV braucht eine Spalte 'Website'.")
