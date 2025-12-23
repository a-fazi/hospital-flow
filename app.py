"""
HospitalFlow - Krankenhaus-Betriebsdashboard
Moderne Streamlit-Anwendung für Krankenhauspersonal mit Live-Metriken, Vorhersagen und Empfehlungen
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, timezone
import pandas as pd
import random
from zoneinfo import ZoneInfo
from db import HospitalDB
from utils import (
    format_time_ago, get_severity_color, get_priority_color, get_risk_color,
    get_status_color, calculate_inventory_status, calculate_capacity_status,
    format_duration_minutes, get_department_color, get_system_status,
    get_metric_severity_for_load, get_metric_severity_for_count, get_metric_severity_for_free,
    get_explanation_score_color
)
from simulation import get_simulation
from ui.styling import apply_custom_styles
from ui.components import render_badge, render_empty_state

# ===== TIMEZONE CONFIGURATION =====
# Set your local timezone here (e.g., 'Europe/Berlin', 'Europe/Vienna', 'America/New_York', 'Asia/Tokyo')
# For Central European Time (CET/CEST), use 'Europe/Berlin' or 'Europe/Zurich'
LOCAL_TIMEZONE = 'Europe/Berlin'  # Change this to your timezone

def get_local_time():
    """Get current time in configured local timezone"""
    return datetime.now(timezone.utc).astimezone(ZoneInfo(LOCAL_TIMEZONE))
# ===================================

# Seitenkonfiguration
st.set_page_config(
    page_title="HospitalFlow",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Leistung: Deaktiviere Neustart bei Widget-Interaktion, um Flackern zu vermeiden
if 'rerun_disabled' not in st.session_state:
    st.session_state.rerun_disabled = False

# Styling anwenden
apply_custom_styles()

# Datenbank initialisieren (für Leistung gecacht)
@st.cache_resource
def init_db():
    return HospitalDB()

db = init_db()

# Navigation mit Icons
PAGES = {
    "📊 Dashboard": "dashboard",
    "📈 Live-Metriken": "metrics",
    "🔮 Vorhersagen": "predictions",
    "⚙️ Betrieb": "operations",

    "🚑 Transport": "transport",
    "📦 Inventar": "inventory",
    "🔧 Gerätewartung": "devices",
    "🏥 Entlassungsplanung": "discharge",
    "🚪 Entlassung": "discharge_tracker",
    "📋 Kapazitätsübersicht": "capacity",
    "💼 Vermögenswerte": "assets"
}

# Systemstatus abrufen
system_status, status_color = get_system_status()


# HospitalFlow title in sidebar (top left, above Demo-Modus)
st.sidebar.markdown("""
<div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1.5rem;">
    <span style="font-size: 2rem;">🏥</span>
    <span style="font-size: 1.5rem; font-weight: 700; color: #4f46e5; letter-spacing: -0.025em;">HospitalFlow</span>
</div>
""", unsafe_allow_html=True)

# Demo Mode toggle (in sidebar - below HospitalFlow)
st.sidebar.markdown("---")
demo_mode = st.sidebar.toggle("🎬 Demo-Modus", value=False, help="Erhöht die Ereignisfrequenz für Demonstrationszwecke")
if demo_mode:
    st.sidebar.info("Demo-Modus: Ereignisse treten häufiger auf")
st.sidebar.markdown("---")



# Sidebar navigation with professional styling
st.sidebar.markdown("""
<div style="padding: 0.5rem 0 1.5rem 0; border-bottom: 1px solid #e5e7eb; margin-bottom: 1rem;">
    <h3 style="color: #667eea; margin: 0; font-size: 1.125rem; font-weight: 600; letter-spacing: -0.01em;">Navigation</h3>
</div>
""", unsafe_allow_html=True)

# Severity Legend (compact and professional)
st.sidebar.markdown("""
<div class="legend" style="margin-bottom: 1rem;">
    <div style="font-size: 0.7rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem; font-weight: 600;">Schweregrad</div>
    <div class="legend-item">
        <span class="badge" style="background: #DC2626; color: white; width: 10px; height: 10px; padding: 0; border-radius: 50%; display: inline-block;"></span>
        <span style="font-size: 0.75rem;">Hoch</span>
    </div>
    <div class="legend-item">
        <span class="badge" style="background: #F59E0B; color: white; width: 10px; height: 10px; padding: 0; border-radius: 50%; display: inline-block;"></span>
        <span style="font-size: 0.75rem;">Mittel</span>
    </div>
    <div class="legend-item">
        <span class="badge" style="background: #10B981; color: white; width: 10px; height: 10px; padding: 0; border-radius: 50%; display: inline-block;"></span>
        <span style="font-size: 0.75rem;">Niedrig</span>
    </div>
</div>
""", unsafe_allow_html=True)
st.sidebar.markdown("---")

# Seitenauswahl mit Icons
page_key = st.sidebar.radio(
    "Seite auswählen",
    list(PAGES.keys()),
    label_visibility="collapsed",
    key="nav_radio"
)

# Seitennamen ohne Icon extrahieren
page = page_key.split(" ", 1)[1] if " " in page_key else page_key

# Professioneller Seiten-Header
page_timestamp = get_local_time().strftime('%H:%M:%S')
st.markdown(f"""
<div class="page-header">
    <h1 class="page-title">{page}</h1>
    <p class="page-subtitle">Zuletzt aktualisiert: {page_timestamp}</p>
</div>
""", unsafe_allow_html=True)

# Simulation initialisieren (pro Sitzung gecacht)
if 'simulation' not in st.session_state:
    st.session_state.simulation = get_simulation()

sim = st.session_state.simulation

# Simulationsstatus aktualisieren (nur wenn genug Zeit vergangen ist, um Flackern zu vermeiden)
if 'last_sim_update' not in st.session_state:
    st.session_state.last_sim_update = datetime.now(timezone.utc)

time_since_update = (datetime.now(timezone.utc) - st.session_state.last_sim_update).total_seconds()
if time_since_update > 2:  # Maximal alle 2 Sekunden aktualisieren
    sim.update()
    st.session_state.last_sim_update = datetime.now(timezone.utc)

# Auf Auslastungsereignisse prüfen (zufällige Chance, aber nicht zu häufig)
if 'last_surge_check' not in st.session_state:
    st.session_state.last_surge_check = datetime.now(timezone.utc)

time_since_last_check = (datetime.now(timezone.utc) - st.session_state.last_surge_check).total_seconds()
# Im Demo-Modus häufiger prüfen (alle 1 Minute statt 5 Minuten)
check_interval = 60 if demo_mode else 300
if time_since_last_check > check_interval:
    if sim.should_trigger_surge(demo_mode=demo_mode):
        sim.trigger_surge_event(intensity=random.uniform(0.7, 1.0))
    st.session_state.last_surge_check = datetime.now(timezone.utc)

# Datenabruf cachen, um Flackern zu vermeiden
@st.cache_data(ttl=5)  # Cache für 5 Sekunden
def get_cached_alerts():
    return db.get_active_alerts()

@st.cache_data(ttl=5)
def get_cached_recommendations():
    return db.get_pending_recommendations()

@st.cache_data(ttl=5)
def get_cached_capacity():
    return db.get_capacity_overview()

# Seitenmodule importieren
from ui.pages import dashboard, operations, metrics, predictions, transport, inventory, devices, discharge_planning, discharge_tracker, capacity, assets

# Seiteninhalt - Routing zu Seitenmodulen
if page == "Dashboard":
    dashboard.render(db, sim, get_cached_alerts, get_cached_recommendations, get_cached_capacity)
elif page == "Betrieb":
    operations.render(db, sim, get_cached_alerts, get_cached_recommendations, get_cached_capacity)
elif page == "Live-Metriken":
    metrics.render(db, sim)
elif page == "Vorhersagen":
    predictions.render(db, sim)
elif page == "Transport":
    transport.render(db, sim)
elif page == "Inventar":
    inventory.render(db, sim)
elif page == "Gerätewartung":
    devices.render(db, sim)
elif page == "Entlassungsplanung":
    discharge_planning.render(db, sim)
elif page == "Entlassung":
    discharge_tracker.render(db, sim)
elif page == "Kapazitätsübersicht":
    capacity.render(db, sim)
elif page == "Vermögenswerte":
    assets.render(db, sim)

# Sidebar-Footer
st.sidebar.markdown("---")
st.sidebar.markdown("")  # Spacing

if st.sidebar.button("🔄 Daten aktualisieren", use_container_width=True):
    st.rerun()

st.sidebar.markdown("")  # Spacing
st.sidebar.markdown("""
<div style="font-size: 0.75rem; color: #9ca3af; padding: 0.5rem 0; line-height: 1.6;">
    <p style="margin: 0.25rem 0;"><strong>HospitalFlow MVP v1.0</strong></p>
    <p style="margin: 0.25rem 0;">Nur aggregierte Daten</p>
    <p style="margin: 0.25rem 0;">Keine personenbezogenen Daten</p>
</div>
""", unsafe_allow_html=True)

# Professioneller Footer mit Datenschutz & Ethik
footer_timestamp = get_local_time().strftime('%Y-%m-%d %H:%M:%S')
st.markdown(f"""
<div class="footer">
    <div class="footer-content">
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 2.5rem; margin-bottom: 2rem;">
            <div>
                <h4 style="color: #111827; font-size: 0.9375rem; font-weight: 700; margin-bottom: 1rem; letter-spacing: -0.01em;">Datenschutz</h4>
                <p style="color: #4b5563; font-size: 0.8125rem; line-height: 1.7; margin: 0;">
                    Alle angezeigten Daten sind aggregiert und anonymisiert. Es werden keine personenbezogenen Gesundheitsdaten (PHI) oder Patientenkennungen gespeichert oder angezeigt. Die Daten dienen ausschließlich operativen Einblicken.
                </p>
            </div>
            <div>
                <h4 style="color: #111827; font-size: 0.9375rem; font-weight: 700; margin-bottom: 1rem; letter-spacing: -0.01em;">Ethik</h4>
                <p style="color: #4b5563; font-size: 0.8125rem; line-height: 1.7; margin: 0;">
                    KI-Empfehlungen sind lediglich Vorschläge. Alle Entscheidungen verbleiben beim Menschen. Das Personal behält die volle Kontrolle über Entscheidungen zur Patientenversorgung. Das System unterstützt, ersetzt aber niemals das klinische Urteilsvermögen.
                </p>
            </div>
            <div>
                <h4 style="color: #111827; font-size: 0.9375rem; font-weight: 700; margin-bottom: 1rem; letter-spacing: -0.01em;">Datennutzung</h4>
                <p style="color: #4b5563; font-size: 0.8125rem; line-height: 1.7; margin: 0;">
                    Kennzahlen, Prognosen und Empfehlungen basieren auf Mustern operativer Daten. Alle Aktionen werden im Prüfprotokoll für Transparenz und Nachvollziehbarkeit protokolliert.
                </p>
            </div>
        </div>
        <div style="text-align: center; padding-top: 1.5rem; border-top: 1px solid #e5e7eb;">
            <p style="color: #9ca3af; font-size: 0.75rem; margin: 0; font-weight: 500;">
                HospitalFlow MVP v1.0 • Entwickelt für den Krankenhausbetrieb • Letzte Aktualisierung: {footer_timestamp}
            </p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

