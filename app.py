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
        # Säuberung der URL
        clean_url = url.strip()
        if not clean_url.startswith('http'):
            clean_url = 'https://' + clean_url
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        start_time = time.time()
        # Timeout erhöht auf 10 Sek für langsamere Handwerker-Seiten
        response = requests.get(clean_url, timeout=10, headers=headers, verify=True)
        ttfb = time.time() - start_time
        
        soup = BeautifulSoup(response.text, 'html.parser')
        score = 100
        issues = []
        
        if ttfb > 1.5:
            score -= 30
            issues.append(f"Performance: {round(ttfb, 2)}s Ladezeit.")
        if not soup.find('h1'):
            score -= 20
            issues.append("SEO: Keine H1-Überschrift.")
        if not soup.find('meta', attrs={'name': 'description'}):
            score -= 15
            issues.append("Marketing: Meta-Description fehlt.")
            
        return max(score, 0), issues, round(ttfb, 2)
    except Exception as e:
        # Rückgabe von 1 statt 0, um "technisch vorhanden, aber Fehler" zu markieren
        return 1, [f"Seite nicht erreichbar: {str(e)[:50]}..."], None

# --- 2. PDF GENERATOR ---
def create_pdf_report(url, score, issues):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 20)
    pdf.set_text_color(0, 255, 65) 
    pdf.cell(w=pdf.epw, h=20, text="AGENT-BOT.DE AUDIT REPORT", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.set_font("helvetica", 'B', 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(w=pdf.epw, h=10, text=f"Analyse fuer: {url}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)
    pdf.set_font("helvetica", 'B', 16)
    pdf.cell(w=pdf.epw, h=10, text=f"Gesamt-Score: {score}/100", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(10)
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(w=pdf.epw, h=10, text="Gefundene Schwachstellen:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("helvetica", size=11)
    for issue in issues:
        safe_issue = issue.replace('ü','ue').replace('ä','ae').replace('ö','oe').replace('ß','ss')
        pdf.multi_cell(w=pdf.epw, h=8, text=f"- {safe_issue}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    return pdf.output()

# --- 3. UI SETUP ---
st.set_page_config(page_title="Agent-Bot.de", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stButton>button { background-color: #00ff41; color: black; font-weight: bold; width: 100%; border-radius: 8px; }
    h1, h2, h3 { color: #00ff41 !important; }
    [data-testid="stMetricValue"] { color: #00ff41 !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 Agent-Bot Lead-Generator")

tab1, tab2 = st.tabs(["🎯 Einzel-Audit", "🔥 Bulk-Check"])

with tab1:
    url_input = st.text_input("Website URL:", placeholder="z.B. https://schreinerei-koeln.de")
    if st.button("Jetzt analysieren"):
        if url_input:
            with st.spinner('Analysiere Infrastruktur...'):
                score, issues, ttfb = grade_website(url_input)
                if score is not None:
                    st.metric("Web-Health Score", f"{score}/100")
                    for issue in issues:
                        st.write(f"🚩 {issue}")
                    pdf_output = create_pdf_report(url_input, score, issues)
                    st.download_button(label="📥 Audit-Report als PDF", data=bytes(pdf_output), file_name="audit.pdf", mime="application/pdf")

with tab2:
    st.write("### 🏭 Köln-Analyse Center")
    uploaded_file = st.file_uploader("Leads (CSV) hochladen", type="csv")
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        if 'Website' in df.columns:
            if st.button("🚀 Audit & Köln-Map starten"):
                results = []
                bar = st.progress(0)
                status = st.empty()
                
                for i, row in df.iterrows():
                    status.text(f"Prüfe: {row['Name']}...")
                    s, _, _ = grade_website(row['Website'])
                    results.append(s if s is not None else 0)
                    bar.progress((i + 1) / len(df))
                
                df['Score'] = results
                status.success("✅ Analyse abgeschlossen!")
                
                st.divider()
                st.write("### 📍 Opportunity-Map Köln")
                
                geolocator = Nominatim(user_agent="agent_bot_final")
                map_list = []
                
                with st.spinner('Punkte auf Karte einzeichnen...'):
                    for idx, row in df.iterrows():
                        try:
                            # Adress-Säuberung für bessere Trefferquote
                            addr = str(row['Adresse'])
                            if "Köln" not in addr: addr += ", Köln"
                            
                            loc = geolocator.geocode(addr, timeout=5)
                            if loc:
                                # Farbe basierend auf Score
                                color = [255, 0, 0, 180] if row['Score'] < 50 else [0, 255, 0, 180]
                                map_list.append({
                                    "Name": row['Name'],
                                    "lat": loc.latitude,
                                    "lon": loc.longitude,
                                    "Score": row['Score'],
                                    "color": color
                                })
                        except: continue
                
                if map_list:
                    map_df = pd.DataFrame(map_list)
                    # Wir nutzen ein Standard-Style, das keine Keys benötigt
                    st.pydeck_chart(pdk.Deck(
                        map_style='light', 
                        initial_view_state=pdk.ViewState(
                            latitude=50.9375, 
                            longitude=6.9603, 
                            zoom=11, 
                            pitch=40
                        ),
                        layers=[
                            pdk.Layer(
                                'ScatterplotLayer',
                                data=map_df,
                                get_position='[lon, lat]',
                                get_color='color',
                                get_radius=200,
                                pickable=True
                            ),
                        ],
                        tooltip={"text": "{Name}\nScore: {Score}/100"}
                    ))
                
                st.write("### 📊 Detail-Liste")
                st.dataframe(df.sort_values(by='Score'), use_container_width=True)
        else:
            st.error("CSV braucht die Spalte 'Website'.")
