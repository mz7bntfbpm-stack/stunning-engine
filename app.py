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
<<<<<<< HEAD
    st.write("Lade deine CSV hoch (Spalte 'Website' erforderlich).")
    uploaded_file = st.file_uploader("Leads hochladen", type="csv")
=======
    st.write("### 🏭 Lead-Fabrik: Bulk-Audit & Karte")
    st.write("Lade hier deine lokal erzeugte 'leads_koeln.csv' hoch.")
    
    uploaded_file = st.file_uploader("Leads hochladen", type="csv")
    
>>>>>>> a69fd17 (feat: add cologne heatmap and enhanced bulk-audit)
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        
        if 'Website' in df.columns:
<<<<<<< HEAD
            if st.button("Liste grillen"):
                results = []
                bar = st.progress(0)
                for i, row in df.iterrows():
=======
            if st.button("🚀 Gesamte Liste grillen & Karte zeichnen"):
                results = []
                # Fortschrittsbalken für das Audit
                bar = st.progress(0)
                status_text = st.empty()
                
                for i, row in df.iterrows():
                    status_text.text(f"Auditiere: {row['Name']}")
>>>>>>> a69fd17 (feat: add cologne heatmap and enhanced bulk-audit)
                    s, _, _ = grade_website(row['Website'])
                    results.append(s if s is not None else 0)
                    bar.progress((i + 1) / len(df))
                df['Score'] = results
<<<<<<< HEAD
                st.dataframe(df.sort_values(by='Score'))
        else:
            st.error("Spalte 'Website' fehlt in der CSV!")
=======
                status_text.success("✅ Audit abgeschlossen!")
                
                # --- JETZT KOMMT DIE KARTE ---
                st.divider()
                st.write("### 📍 Opportunity-Map Köln")
                
                # Geocoding & Karten-Logik
                # Hinweis: geopy und pydeck müssen in den requirements stehen!
                from geopy.geocoders import Nominatim
                import pydeck as pdk

                geolocator = Nominatim(user_agent="agent_bot_hannes")
                
                def get_coords(addr):
                    try:
                        # Wir hängen "Köln" an, um die Suche einzugrenzen
                        loc = geolocator.geocode(f"{addr}")
                        return (loc.latitude, loc.longitude) if loc else (None, None)
                    except:
                        return None, None

                with st.spinner('Verorte Leads auf der Karte...'):
                    # Wir fügen Koordinaten nur für die Karte hinzu
                    coords = [get_coords(a) for a in df['Adresse']]
                    df['lat'] = [c[0] for c in coords]
                    df['lon'] = [c[1] for c in coords]
                    
                    # Filter: Nur Einträge mit gültigen Koordinaten
                    map_df = df.dropna(subset=['lat', 'lon'])
                    
                    # Farb-Logik: Rot für schlechte Scores (<50), Grün für gute
                    map_df['color'] = map_df['Score'].apply(lambda x: [255, 0, 0, 160] if x < 50 else [0, 255, 0, 160])

                    st.pydeck_chart(pdk.Deck(
                        map_style='mapbox://styles/mapbox/dark-v9',
                        initial_view_state=pdk.ViewState(
                            latitude=50.9375, 
                            longitude=6.9603, 
                            zoom=11, 
                            pitch=45
                        ),
                        layers=[
                            pdk.Layer(
                                'ScatterplotLayer',
                                data=map_df,
                                get_position='[lon, lat]',
                                get_color='color',
                                get_radius=180,
                                pickable=True
                            ),
                        ],
                        tooltip={"text": "{Name}\nScore: {Score}"}
                    ))

                # Tabelle der Ergebnisse anzeigen
                st.write("### Analyse-Ergebnisse")
                st.dataframe(df.sort_values(by='Score'), use_container_width=True)
        else:
            st.error("Spalte 'Website' fehlt in der CSV! Hast du den Scraper richtig laufen lassen?")
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
>>>>>>> a69fd17 (feat: add cologne heatmap and enhanced bulk-audit)
