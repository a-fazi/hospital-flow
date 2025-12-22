"""
HospitalFlow - Hospital Operations Dashboard
Modern Streamlit app for hospital staff with live metrics, predictions, and recommendations
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import random
from db import HospitalDB
from utils import (
    format_time_ago, get_severity_color, get_priority_color, get_risk_color,
    get_status_color, calculate_inventory_status, calculate_capacity_status,
    format_duration_minutes, get_department_color, get_system_status,
    get_metric_severity_for_load, get_metric_severity_for_count, get_metric_severity_for_free,
    get_explanation_score_color
)
from simulation import get_simulation

# Page config
st.set_page_config(
    page_title="HospitalFlow",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Performance: Disable rerun on widget interaction to prevent flickering
if 'rerun_disabled' not in st.session_state:
    st.session_state.rerun_disabled = False

# Helper function for severity badges
def render_badge(text: str, severity: str = "low") -> str:
    """Render a consistent severity badge (green/yellow/red pill)"""
    color = get_severity_color(severity)
    return f'<span class="badge" style="background: {color}; color: white;">{text}</span>'

# Custom CSS for professional UI
st.markdown("""
<style>
    /* Professional Typography */
    * {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', Roboto, 'Helvetica Neue', Arial, sans-serif;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-weight: 600;
        letter-spacing: -0.02em;
        color: #111827;
        line-height: 1.2;
    }
    
    /* Main container - professional spacing */
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1600px;
    }
    
    /* Professional Sticky Header */
    .sticky-header {
        position: sticky;
        top: -1rem;
        z-index: 999;
        background: linear-gradient(to bottom, #ffffff 0%, #fafbfc 100%);
        border-bottom: 2px solid #e5e7eb;
        padding: 1.25rem 0;
        margin: -1rem 0 2rem 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        backdrop-filter: blur(10px);
    }
    
    .header-content {
        display: flex;
        justify-content: space-between;
        align-items: center;
        max-width: 1600px;
        margin: 0 auto;
        padding: 0 2rem;
    }
    
    .header-title {
        font-size: 1.625rem;
        font-weight: 700;
        color: #4f46e5;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        letter-spacing: -0.025em;
    }
    
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.8);
    }
    
    /* Professional Page Header */
    .page-header {
        margin-bottom: 2.5rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid #e5e7eb;
    }
    
    .page-title {
        font-size: 2.25rem;
        font-weight: 700;
        color: #111827;
        margin: 0 0 0.5rem 0;
        letter-spacing: -0.03em;
    }
    
    .page-subtitle {
        font-size: 0.9375rem;
        color: #6b7280;
        margin: 0;
        font-weight: 400;
    }
    
    /* Professional Metric Cards */
    .metric-card {
        background: linear-gradient(to bottom, #ffffff 0%, #fafbfc 100%);
        padding: 1.75rem;
        border-radius: 16px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
        border: 1px solid #e5e7eb;
        border-left: 4px solid #667eea;
        transition: all 0.2s ease;
        position: relative;
        overflow: hidden;
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        opacity: 0;
        transition: opacity 0.2s;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 2px 4px rgba(0, 0, 0, 0.06);
    }
    
    .metric-card:hover::before {
        opacity: 1;
    }
    
    .metric-value {
        font-size: 2.25rem;
        font-weight: 700;
        color: #111827;
        margin: 0.75rem 0;
        line-height: 1.1;
        letter-spacing: -0.02em;
    }
    
    .metric-label {
        font-size: 0.8125rem;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-weight: 600;
    }
    
    /* Professional Badges */
    .badge {
        display: inline-flex;
        align-items: center;
        padding: 0.4375rem 0.875rem;
        border-radius: 12px;
        font-size: 0.6875rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        line-height: 1;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
    }
    
    /* Professional Tables */
    .dataframe {
        border-radius: 12px;
        overflow: hidden;
        font-size: 0.875rem;
        border: 1px solid #e5e7eb;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
    
    /* Professional Empty States */
    .empty-state {
        text-align: center;
        padding: 4rem 2rem;
        color: #9ca3af;
        background: linear-gradient(to bottom, #fafbfc 0%, #f9fafb 100%);
        border-radius: 16px;
        border: 2px dashed #d1d5db;
        margin: 2rem 0;
    }
    
    .empty-state-icon {
        font-size: 4rem;
        margin-bottom: 1.25rem;
        opacity: 0.4;
        filter: grayscale(20%);
    }
    
    .empty-state-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: #4b5563;
        margin-bottom: 0.75rem;
        letter-spacing: -0.01em;
    }
    
    .empty-state-text {
        font-size: 0.9375rem;
        color: #9ca3af;
        line-height: 1.6;
    }
    
    /* Professional Footer */
    .footer {
        margin-top: 4rem;
        padding: 3rem 0 2rem 0;
        border-top: 2px solid #e5e7eb;
        background: linear-gradient(to bottom, #fafbfc 0%, #ffffff 100%);
    }
    
    .footer-content {
        max-width: 1600px;
        margin: 0 auto;
        padding: 0 2rem;
    }
    
    /* Professional Legend */
    .legend {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        padding: 1rem;
        background: linear-gradient(to bottom, #ffffff 0%, #fafbfc 100%);
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        font-size: 0.75rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
    
    .legend-item {
        display: flex;
        align-items: center;
        gap: 0.625rem;
        padding: 0.25rem 0;
    }
    
    /* Professional Timestamp */
    .timestamp {
        font-size: 0.75rem;
        color: #6b7280;
        font-weight: 500;
        letter-spacing: 0.02em;
    }
    
    /* Professional Cards */
    .info-card {
        background: linear-gradient(to bottom, #ffffff 0%, #fafbfc 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
        transition: all 0.2s ease;
    }
    
    .info-card:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        transform: translateY(-1px);
    }
    
    /* Professional Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    /* Professional Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(to bottom, #ffffff 0%, #fafbfc 100%);
        border-right: 1px solid #e5e7eb;
    }
    
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    
    /* Professional Readability */
    p {
        line-height: 1.7;
        color: #374151;
    }
    
    /* Better column spacing */
    [data-testid="column"] {
        padding: 0 1rem;
    }
    
    /* Professional Section Dividers */
    hr {
        border: none;
        border-top: 1px solid #e5e7eb;
        margin: 2rem 0;
    }
    
    /* Smooth scrolling */
    html {
        scroll-behavior: smooth;
    }
    
    /* Professional Input Fields */
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 1px solid #d1d5db;
        transition: all 0.2s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Professional Selectboxes */
    .stSelectbox > div > div {
        border-radius: 8px;
    }
    
    /* Loading states */
    .stSpinner > div {
        border-color: #667eea transparent transparent transparent;
    }
</style>
""", unsafe_allow_html=True)

# Initialize database (cached for performance)
@st.cache_resource
def init_db():
    return HospitalDB()

db = init_db()

# Helper function for empty states
def render_empty_state(icon: str, title: str, text: str):
    """Render a consistent empty state"""
    return f"""
    <div class="empty-state">
        <div class="empty-state-icon">{icon}</div>
        <div class="empty-state-title">{title}</div>
        <div class="empty-state-text">{text}</div>
    </div>
    """

# Navigation with icons
PAGES = {
    "📊 Dashboard": "dashboard",
    "📈 Live-Metriken": "metrics",
    "🔮 Vorhersagen": "predictions",
    "⚙️ Betrieb": "operations",
    "🚨 Warnungen": "alerts",
    "💡 Empfehlungen": "recommendations",
    "🚑 Transport": "transport",
    "📦 Inventar": "inventory",
    "🔧 Gerätewartung": "devices",
    "🏥 Entlassungsplanung": "discharge",
    "🚪 Entlassung": "discharge_tracker",
    "📋 Kapazitätsübersicht": "capacity",
    "📝 Prüfprotokoll": "audit",
    "💼 Vermögenswerte": "assets"
}

# Get system status
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

# Page selection with icons
page_key = st.sidebar.radio(
    "Select page",
    list(PAGES.keys()),
    label_visibility="collapsed",
    key="nav_radio"
)

# Extract page name without icon
page = page_key.split(" ", 1)[1] if " " in page_key else page_key

# Professional Page Header
page_timestamp = datetime.now().strftime('%H:%M:%S')
st.markdown(f"""
<div class="page-header">
    <h1 class="page-title">{page}</h1>
    <p class="page-subtitle">Zuletzt aktualisiert: {page_timestamp}</p>
</div>
""", unsafe_allow_html=True)

# Initialize simulation (cached per session)
if 'simulation' not in st.session_state:
    st.session_state.simulation = get_simulation()

sim = st.session_state.simulation

# Update simulation state (only if enough time has passed to prevent flickering)
if 'last_sim_update' not in st.session_state:
    st.session_state.last_sim_update = datetime.now()

time_since_update = (datetime.now() - st.session_state.last_sim_update).total_seconds()
if time_since_update > 2:  # Update every 2 seconds max
    sim.update()
    st.session_state.last_sim_update = datetime.now()

# Check for surge events (random chance, but not too frequently)
if 'last_surge_check' not in st.session_state:
    st.session_state.last_surge_check = datetime.now()

time_since_last_check = (datetime.now() - st.session_state.last_surge_check).total_seconds()
# In demo mode, check more frequently (every 1 minute vs 5 minutes)
check_interval = 60 if demo_mode else 300
if time_since_last_check > check_interval:
    if sim.should_trigger_surge(demo_mode=demo_mode):
        sim.trigger_surge_event(intensity=random.uniform(0.7, 1.0))
    st.session_state.last_surge_check = datetime.now()

# Cache data fetching to prevent flickering
@st.cache_data(ttl=5)  # Cache for 5 seconds
def get_cached_alerts():
    return db.get_active_alerts()

@st.cache_data(ttl=5)
def get_cached_recommendations():
    return db.get_pending_recommendations()

@st.cache_data(ttl=5)
def get_cached_capacity():
    return db.get_capacity_overview()

# Page content
if page == "Dashboard":
    # Get data (cached to prevent flickering)
    alerts = get_cached_alerts()
    recommendations = get_cached_recommendations()
    capacity = get_cached_capacity()
    transport = db.get_transport_requests()
    inventory = db.get_inventory_status()
    devices = db.get_device_maintenance_risks()
    predictions = db.get_predictions(15)
    
    # Get simulated metrics (correlated)
    sim_metrics = sim.get_current_metrics()
    
    # Calculate dashboard metrics using simulation
    # ED Load (from simulation)
    ed_load = sim_metrics['ed_load']
    ed_severity, ed_hint = get_metric_severity_for_load(ed_load)
    
    # Waiting count (from simulation - correlated with ED load)
    waiting_count = int(sim_metrics['waiting_count'])
    waiting_severity, waiting_hint = get_metric_severity_for_count(waiting_count, {'critical': 20, 'watch': 10})
    
    # Beds free (from simulation - inversely correlated with ED load)
    beds_free = int(sim_metrics['beds_free'])
    total_beds = sum([c['total_beds'] for c in capacity]) if capacity else 100
    beds_severity, beds_hint = get_metric_severity_for_free(beds_free, total_beds)
    
    # Staff load (from simulation - correlated with ED load)
    staff_load = sim_metrics['staff_load']
    staff_severity, staff_hint = get_metric_severity_for_load(staff_load)
    
    # Rooms free (from simulation - correlated with beds free)
    rooms_free = int(sim_metrics['rooms_free'])
    total_rooms = 45
    rooms_severity, rooms_hint = get_metric_severity_for_free(rooms_free, total_rooms)
    
    # OR load (from simulation)
    or_load = sim_metrics['or_load']
    or_severity, or_hint = get_metric_severity_for_load(or_load)
    
    # Transport queue (from simulation - delayed correlation with ED load)
    transport_queue = int(sim_metrics['transport_queue'])
    transport_severity, transport_hint = get_metric_severity_for_count(transport_queue, {'critical': 8, 'watch': 5})
    
    # Inventory/Device risk (count of high-risk items)
    low_inventory = len([i for i in inventory if i['current_stock'] < i['min_threshold']])
    high_risk_devices = len([d for d in devices if d['risk_level'] == 'high'])
    risk_count = low_inventory + high_risk_devices
    risk_severity, risk_hint = get_metric_severity_for_count(risk_count, {'critical': 5, 'watch': 3})
    
    # Check for active surge events
    active_surges = [e for e in sim.active_events if e['type'] == 'surge']
    if active_surges:
        surge = active_surges[0]
        elapsed = (datetime.now() - surge['start_time']).total_seconds() / 60
        remaining = max(0, surge['duration_minutes'] - elapsed)
        st.warning(f"⚠️ **Aktives Auslastungsereignis**: Noch {remaining:.0f} Minuten verbleibend (Intensität: {surge['intensity']:.1f})")
        st.markdown("")  # Spacing
    
    # Live Status Section
    st.markdown("### Live Status")
    st.markdown("")  # Abstand
    
    # 8 Metric Cards in 4x2 grid
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        severity_color = get_severity_color(ed_severity)
        badge_html = render_badge(ed_hint, ed_severity)
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: {severity_color};">
            <div style="font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600; margin-bottom: 0.75rem;">Notaufnahme-Auslastung</div>
            <div style="font-size: 2.5rem; font-weight: 700; color: #111827; margin: 0.75rem 0; letter-spacing: -0.02em;">{ed_load:.0f}%</div>
            <div style="margin-top: 1rem;">
                {badge_html}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        severity_color = get_severity_color(waiting_severity)
        badge_html = render_badge(waiting_hint, waiting_severity)
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: {severity_color};">
            <div style="font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600; margin-bottom: 0.75rem;">Wartende Patienten</div>
            <div style="font-size: 2.5rem; font-weight: 700; color: #111827; margin: 0.75rem 0; letter-spacing: -0.02em;">{waiting_count}</div>
            <div style="margin-top: 1rem;">
                {badge_html}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        severity_color = get_severity_color(beds_severity)
        badge_html = render_badge(beds_hint, beds_severity)
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: {severity_color};">
            <div style="font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600; margin-bottom: 0.75rem;">Freie Betten</div>
            <div style="font-size: 2.5rem; font-weight: 700; color: #111827; margin: 0.75rem 0; letter-spacing: -0.02em;">{beds_free}</div>
            <div style="margin-top: 1rem;">
                {badge_html}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        severity_color = get_severity_color(staff_severity)
        badge_html = render_badge(staff_hint, staff_severity)
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: {severity_color};">
            <div style="font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600; margin-bottom: 0.75rem;">Personal-Auslastung</div>
            <div style="font-size: 2.5rem; font-weight: 700; color: #111827; margin: 0.75rem 0; letter-spacing: -0.02em;">{staff_load:.0f}%</div>
            <div style="margin-top: 1rem;">
                {badge_html}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Second row of metric cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        severity_color = get_severity_color(rooms_severity)
        badge_html = render_badge(rooms_hint, rooms_severity)
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: {severity_color};">
            <div style="font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600; margin-bottom: 0.75rem;">Freie Räume</div>
            <div style="font-size: 2.5rem; font-weight: 700; color: #111827; margin: 0.75rem 0; letter-spacing: -0.02em;">{rooms_free}</div>
            <div style="margin-top: 1rem;">
                {badge_html}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        severity_color = get_severity_color(or_severity)
        badge_html = render_badge(or_hint, or_severity)
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: {severity_color};">
            <div style="font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600; margin-bottom: 0.75rem;">OP-Auslastung</div>
            <div style="font-size: 2.5rem; font-weight: 700; color: #111827; margin: 0.75rem 0; letter-spacing: -0.02em;">{or_load:.0f}%</div>
            <div style="margin-top: 1rem;">
                {badge_html}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        severity_color = get_severity_color(transport_severity)
        badge_html = render_badge(transport_hint, transport_severity)
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: {severity_color};">
            <div style="font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600; margin-bottom: 0.75rem;">Transport-Warteschlange</div>
            <div style="font-size: 2.5rem; font-weight: 700; color: #111827; margin: 0.75rem 0; letter-spacing: -0.02em;">{transport_queue}</div>
            <div style="margin-top: 1rem;">
                {badge_html}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        severity_color = get_severity_color(risk_severity)
        badge_html = render_badge(risk_hint, risk_severity)
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: {severity_color};">
            <div style="font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600; margin-bottom: 0.75rem;">Bestands-/Geräterisiko</div>
            <div style="font-size: 2.5rem; font-weight: 700; color: #111827; margin: 0.75rem 0; letter-spacing: -0.02em;">{risk_count}</div>
            <div style="margin-top: 1rem;">
                {badge_html}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Charts and Outlook Panel
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Charts Section
        st.markdown("### Trends (Letzte 60 Minuten)")
        st.markdown("")  # Spacing
        
        # Get historical data from simulation
        waiting_history = sim.get_metric_history('waiting_count', 60)
        ed_history = sim.get_metric_history('ed_load', 60)
        
        # Convert to DataFrames
        df_waiting = pd.DataFrame(waiting_history)
        df_waiting['timestamp'] = pd.to_datetime(df_waiting['timestamp'])
        
        df_ed = pd.DataFrame(ed_history)
        df_ed['timestamp'] = pd.to_datetime(df_ed['timestamp'])
        
        # Warteschlangen-Diagramm
        fig_waiting = px.line(
            df_waiting,
            x='timestamp',
            y='value',
            title="Wartende Anzahl",
            labels={'value': 'Anzahl', 'timestamp': ''}
        )
        fig_waiting.update_layout(
            height=250,
            margin=dict(l=40, r=20, t=40, b=20),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, showline=False),
            yaxis=dict(showgrid=True, gridcolor='#e5e7eb', showline=False, title=''),
            showlegend=False,
            font=dict(size=11)
        )
        fig_waiting.update_traces(line_color='#667eea', line_width=2.5, marker=dict(size=4))
        st.plotly_chart(fig_waiting, use_container_width=True)
        
        st.markdown("")  # Spacing
        
        # Notaufnahme-Auslastung Diagramm
        fig_ed = px.line(
            df_ed,
            x='timestamp',
            y='value',
            title="Notaufnahme-Auslastung",
            labels={'value': 'Auslastung %', 'timestamp': ''}
        )
        fig_ed.update_layout(
            height=250,
            margin=dict(l=40, r=20, t=40, b=20),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, showline=False),
            yaxis=dict(showgrid=True, gridcolor='#e5e7eb', showline=False, range=[0, 100], title=''),
            showlegend=False,
            font=dict(size=11)
        )
        fig_ed.update_traces(line_color='#DC2626', line_width=2.5, marker=dict(size=4))
        st.plotly_chart(fig_ed, use_container_width=True)
    
    with col2:
        # Next 15 min outlook panel
        st.markdown("### Ausblick: Nächste 15 Minuten")
        st.markdown("")  # Spacing
        
        # Get top 3 predicted bottlenecks
        bottleneck_predictions = []
        for pred in predictions:
            if pred['time_horizon_minutes'] <= 15:
                bottleneck_predictions.append(pred)
        
        # Sort by predicted value (descending) and take top 3
        bottleneck_predictions.sort(key=lambda x: x['predicted_value'], reverse=True)
        top_bottlenecks = bottleneck_predictions[:3]
        
        # German translation for prediction types
        pred_type_map = {
            'patient_arrival': 'Patientenzugang',
            'bed_demand': 'Bettenbedarf',
            'resource_needed': 'Ressourcenbedarf',
            'waiting_count': 'Wartende Patienten',
            'ed_load': 'Notaufnahme-Auslastung',
            'or_load': 'OP-Auslastung',
            'staff_load': 'Personal-Auslastung',
            'transport_queue': 'Transport-Warteschlange',
            'rooms_free': 'Freie Räume',
            'beds_free': 'Freie Betten',
            # Add more as needed
        }
        if top_bottlenecks:
            for i, bottleneck in enumerate(top_bottlenecks, 1):
                pred_type_key = bottleneck['prediction_type']
                pred_type = pred_type_map.get(pred_type_key, pred_type_key.replace('_', ' ').title())
                pred_value = bottleneck['predicted_value']
                pred_minutes = bottleneck['time_horizon_minutes']
                dept = bottleneck.get('department', 'N/A')
                # German translation for department names (add more as needed)
                dept_map = {
                    'ER': 'Notaufnahme',
                    'ICU': 'Intensivstation',
                    'Surgery': 'Chirurgie',
                    'General Ward': 'Allgemeinstation',
                    'Cardiology': 'Kardiologie',
                    'Neurology': 'Neurologie',
                    'Pediatrics': 'Pädiatrie',
                    'Oncology': 'Onkologie',
                    'Orthopedics': 'Orthopädie',
                    'Maternity': 'Geburtshilfe',
                    'Radiology': 'Radiologie',
                    'Other': 'Andere'
                }
                dept_de = dept_map.get(dept, dept)
                # German time string
                if pred_minutes == 1:
                    time_str = f'in {pred_minutes} Minute'
                else:
                    time_str = f'in {pred_minutes} Minuten'
                st.markdown(f"""
                <div style="background: white; padding: 1rem; border-radius: 8px; margin-bottom: 0.75rem; border-left: 3px solid #667eea; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                    <div style="font-size: 0.875rem; font-weight: 600; color: #1f2937; margin-bottom: 0.25rem;">
                        {i}. {pred_type}
                    </div>
                    <div style="font-size: 1.25rem; font-weight: 700; color: #667eea; margin: 0.25rem 0;">
                        {pred_value:.0f}
                    </div>
                    <div style="font-size: 0.75rem; color: #6b7280; margin-top: 0.5rem;">
                        {dept_de} • {time_str}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(render_empty_state("📊", "Keine vorhergesagten Engpässe", "System arbeitet im normalen Bereich"), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Recent alerts
    st.markdown("### Kürzliche Warnungen")
    st.markdown("")  # Abstand
    if alerts:
        severity_de_map = {'high': 'hoch', 'medium': 'mittel', 'low': 'niedrig'}
        for alert in alerts[:5]:
            severity_color = get_severity_color(alert['severity'])
            severity_de = severity_de_map.get(alert['severity'], alert['severity'])
            badge_html = render_badge(severity_de.upper(), alert['severity'])
            st.markdown(f"""
            <div class="info-card" style="border-left: 4px solid {severity_color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex: 1;">
                        <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.75rem;">
                            {badge_html}
                            <strong style="color: #111827; font-size: 0.9375rem; font-weight: 600;">{alert['message']}</strong>
                        </div>
                        <div style="color: #6b7280; font-size: 0.8125rem; font-weight: 500;">
                            {alert.get('department', 'N/A')} • {format_time_ago(alert['timestamp'])}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Keine aktiven Warnungen")
    
    # Ausstehende Empfehlungen
    st.markdown("### Ausstehende Empfehlungen")
    st.markdown("")  # Abstand
    if recommendations:
        priority_de_map = {'high': 'hoch', 'medium': 'mittel', 'low': 'niedrig'}
        for rec in recommendations[:3]:
            priority_color = get_priority_color(rec['priority'])
            priority_de = priority_de_map.get(rec['priority'], rec['priority'])
            badge_html = render_badge(priority_de.upper(), rec['priority'])
            st.markdown(f"""
            <div class="info-card" style="border-left: 4px solid {priority_color};">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div style="flex: 1;">
                        <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.75rem;">
                            {badge_html}
                            <strong style="color: #111827; font-size: 1rem; font-weight: 600;">{rec['title']}</strong>
                        </div>
                        <p style="color: #4b5563; margin-top: 0.5rem; margin-bottom: 0; line-height: 1.7; font-size: 0.9375rem;">{rec['description']}</p>
                        <div style="color: #9ca3af; font-size: 0.75rem; margin-top: 1rem; font-weight: 500;">
                            {rec.get('department', 'N/A')} • {format_time_ago(rec['timestamp'])}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(render_empty_state("✅", "Keine ausstehenden Empfehlungen", "Alle Empfehlungen wurden überprüft"), unsafe_allow_html=True)

elif page == "Betrieb":
    # Operations page with tabs
    tab1, tab2, tab3 = st.tabs(["🚨 Warnungen", "💡 Empfehlungen", "📝 Protokoll"])
    
    # Alerts Tab
    with tab1:
        st.markdown("### Warnungen")
        st.markdown("")  # Spacing
        
        # Filter row
        col1, col2, col3 = st.columns([2, 2, 2])
        
        with col1:
            # Bereich Dropdown mit deutschen Übersetzungen
            all_alerts = db.get_alerts_by_time_range(24)
            dept_map = {
                'ER': 'Notaufnahme',
                'ED': 'Notaufnahme',
                'ICU': 'Intensivstation',
                'Surgery': 'Chirurgie',
                'General Ward': 'Allgemeinstation',
                'Cardiology': 'Kardiologie',
                'Neurology': 'Neurologie',
                'Pediatrics': 'Pädiatrie',
                'Oncology': 'Onkologie',
                'Orthopedics': 'Orthopädie',
                'Maternity': 'Geburtshilfe',
                'Radiology': 'Radiologie',
                'Ward': 'Station',
                'Other': 'Andere',
                'N/A': 'Bereich',
            }
            # Build mapping for all unique departments
            unique_depts = sorted(list(set([a.get('department', 'N/A') for a in all_alerts if a.get('department')])))
            areas_de = [dept_map.get(d, d) for d in unique_depts]
            area_map = dict(zip(areas_de, unique_depts))
            areas_de_display = ["Alle"] + areas_de
            selected_area_de = st.selectbox("Bereich", areas_de_display, key="ops_alert_area")
            selected_area = None if selected_area_de == "Alle" else area_map[selected_area_de]
        
        with col2:
            # Severity chips
            severity_options = ["Alle", "hoch", "mittel", "niedrig"]
            selected_severities = st.multiselect(
                "Schweregrad",
                severity_options,
                default=["hoch", "mittel"],
                key="ops_alert_severity"
            )
            if not selected_severities:
                selected_severities = severity_options
        
        with col3:
            # Zeitspanne
            time_range = st.selectbox(
                "Zeitraum",
                ["Letzte 1 Stunde", "Letzte 6 Stunden", "Letzte 24 Stunden"],
                index=2,
                key="ops_alert_time"
            )
            hours_map = {"Letzte 1 Stunde": 1, "Letzte 6 Stunden": 6, "Letzte 24 Stunden": 24}
            hours = hours_map[time_range]
        
        st.markdown("")  # Spacing
        
        # Get filtered alerts
        alerts = db.get_alerts_by_time_range(hours)
        
        # Apply filters
        filtered_alerts = alerts
        if selected_area is not None:
            filtered_alerts = [a for a in filtered_alerts if a.get('department') == selected_area]
        if "Alle" not in selected_severities:
            filtered_alerts = [a for a in filtered_alerts if a['severity'] in selected_severities]
        
        # Display alerts as compact cards
        if filtered_alerts:
            for alert in filtered_alerts:
                severity_color = get_severity_color(alert['severity'])
                badge_html = render_badge(alert['severity'].upper(), alert['severity'])
                # Get predicted minutes from related predictions if available
                predictions = db.get_predictions(15)
                predicted_minutes = None
                for pred in predictions:
                    if pred.get('department') == alert.get('department') and pred.get('prediction_type') in ['patient_arrival', 'bed_demand', 'resource_needed']:
                        predicted_minutes = pred.get('time_horizon_minutes')
                        break
                # Translate department for display
                dept_map = {
                    'ER': 'Notaufnahme',
                    'ED': 'Notaufnahme',
                    'ICU': 'Intensivstation',
                    'Surgery': 'Chirurgie',
                    'General Ward': 'Allgemeinstation',
                    'Cardiology': 'Kardiologie',
                    'Neurology': 'Neurologie',
                    'Pediatrics': 'Pädiatrie',
                    'Oncology': 'Onkologie',
                    'Orthopedics': 'Orthopädie',
                    'Maternity': 'Geburtshilfe',
                    'Radiology': 'Radiologie',
                    'Ward': 'Station',
                    'Other': 'Andere',
                    'N/A': 'Bereich',
                }
                dept_de = dept_map.get(alert.get('department', 'N/A'), alert.get('department', 'N/A'))
                col1, col2 = st.columns([5, 1])
                with col1:
                    pred_text = f" • Prognose: {predicted_minutes} Min." if predicted_minutes else ""
                    st.markdown(f"""
                    <div style="background: white; padding: 1rem; border-radius: 8px; margin-bottom: 0.75rem; border-left: 4px solid {severity_color}; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                        <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem;">
                            {badge_html}
                            <span style="font-size: 0.75rem; color: #6b7280; font-weight: 500;">{dept_de}</span>
                            <span style="font-size: 0.75rem; color: #9ca3af;">•</span>
                            <span style="font-size: 0.75rem; color: #6b7280;">{format_time_ago(alert['timestamp'])}</span>
                            {f'<span style=\"font-size: 0.75rem; color: #667eea;\">{pred_text}</span>' if predicted_minutes else ''}
                        </div>
                        <div style="font-weight: 600; color: #1f2937; font-size: 0.95rem;">
                            {alert['message']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    if st.button("Bestätigen", key=f"ops_ack_{alert['id']}", use_container_width=True):
                        db.acknowledge_alert(alert['id'])
                        st.success("✅ Warnung bestätigt")
                        st.rerun()
        else:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">🔍</div>
                <div class="empty-state-title">Keine Warnungen gefunden</div>
                <div class="empty-state-text">Keine Warnungen entsprechen den ausgewählten Filtern</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Recommendations Tab
    with tab2:
        st.markdown("### Empfehlungen")
        st.markdown("")  # Abstand
        
        # Rollen-Auswahl oben angeheftet
        selected_role = st.radio(
            "Rolle",
            ["Alle", "Pflegekraft", "Arzt/Ärztin", "Leitung"],
            horizontal=True,
            key="ops_rec_role"
        )
        
        st.markdown("")  # Spacing
        
        # Get recommendations
        recommendations = db.get_pending_recommendations()
        
        # Filter by role (in real app, this would filter by actual role field)
        if selected_role != "Alle":
            # For MVP, we'll show all but could filter by rec_type or department
            pass
        
        # German translation for explanation_score (trust level)
        vertrauen_map = {'high': 'hoch', 'medium': 'mittel', 'low': 'niedrig'}
        if recommendations:
            for rec in recommendations:
                priority_color = get_priority_color(rec['priority'])
                # German translation for priority
                priority_de_map = {'high': 'hoch', 'medium': 'mittel', 'low': 'niedrig'}
                priority_de = priority_de_map.get(rec['priority'], rec['priority'])
                badge_html = render_badge(priority_de.upper(), rec['priority'])

                # Impact tags (extract from department and rec_type)
                impact_tags = []
                if rec.get('department'):
                    impact_tags.append(rec['department'])
                if rec.get('rec_type'):
                    # Translate common rec_types to German
                    rec_type_map = {
                        'capacity': 'Kapazität',
                        'staffing': 'Personal',
                        'inventory': 'Inventar',
                        'general': 'Allgemein',
                    }
                    rec_type = rec['rec_type']
                    impact_tags.append(rec_type_map.get(rec_type, rec_type.replace('_', ' ').title()))

                # Use new template format if available, otherwise fall back to old format
                has_new_format = rec.get('action') and rec.get('reason')

                if has_new_format:
                    st.markdown(f"""
                    <div style="background: white; padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid {priority_color}; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                        <div style="margin-bottom: 1rem;">
                            <h4 style="margin: 0 0 0.5rem 0; color: #1f2937;">{rec['title']}</h4>
                            <div style="margin-bottom: 0.75rem;">{badge_html}</div>
                        </div>
                        <div style="background: #f9fafb; padding: 1rem; border-radius: 6px; margin-bottom: 0.75rem;">
                            <div style="margin-bottom: 0.75rem;">
                                <strong style="color: #1f2937; font-size: 0.875rem;">Maßnahme:</strong>
                                <p style="margin: 0.25rem 0 0 0; color: #4b5563; line-height: 1.6;">{rec.get('action', 'N/A')}</p>
                            </div>
                            <div style="margin-bottom: 0.75rem;">
                                <strong style="color: #1f2937; font-size: 0.875rem;">Begründung:</strong>
                                <p style="margin: 0.25rem 0 0 0; color: #4b5563; line-height: 1.6;">{rec.get('reason', 'N/A')}</p>
                            </div>
                            <div style="margin-bottom: 0.75rem;">
                                <strong style="color: #1f2937; font-size: 0.875rem;">Erwartete Auswirkung:</strong>
                                <p style="margin: 0.25rem 0 0 0; color: #4b5563; line-height: 1.6;">{rec.get('expected_impact', 'N/A')}</p>
                            </div>
                            <div>
                                <strong style="color: #1f2937; font-size: 0.875rem;">Sicherheits-Hinweis:</strong>
                                <p style="margin: 0.25rem 0 0 0; color: #4b5563; line-height: 1.6;">{rec.get('safety_note', 'N/A')}</p>
                            </div>
                        </div>
                        <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                            {' '.join([f'<span class="badge" style="background: #e5e7eb; color: #4b5563;">{tag}</span>' for tag in impact_tags])}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Fallback to old format
                    st.markdown(f"""
                    <div style="background: white; padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid {priority_color}; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                        <div style="display: flex; align-items: start; gap: 0.75rem; margin-bottom: 1rem;">
                            {badge_html}
                            <div style="flex: 1;">
                                <h4 style="margin: 0 0 0.5rem 0; color: #1f2937;">{rec['title']}</h4>
                                <p style="color: #6b7280; margin: 0; line-height: 1.6;">{rec['description']}</p>
                            </div>
                        </div>
                        <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 1rem;">
                            {' '.join([f'<span class="badge" style="background: #e5e7eb; color: #4b5563;">{tag}</span>' for tag in impact_tags])}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Expandable "Why suggested?" section
                with st.expander("Warum vorgeschlagen?", expanded=False):
                    if has_new_format:
                        # Use the reason and expected_impact from the template
                        explanation = f"""
                        <strong>Begründung:</strong> {rec.get('reason', 'N/A')}<br><br>
                        <strong>Erwartete Auswirkung:</strong> {rec.get('expected_impact', 'N/A')}<br><br>
                        """
                    else:
                        # Generate explanation based on rec_type
                        rec_type = rec.get('rec_type', 'general')
                        explanations = {
                            'capacity': f"Die aktuelle Kapazitätsauslastung in {rec.get('department', 'diesem Bereich')} liegt über dem Schwellenwert. Historische Daten zeigen, dass das Öffnen von Überlaufbetten die Wartezeiten um 15-20% reduziert.",
                            'staffing': f"Die Analyse der Personalauslastung zeigt, dass {rec.get('department', 'dieser Bereich')} eine erhöhte Nachfrage erfährt. Eine Umverteilung kann die Reaktionszeiten verbessern.",
                            'inventory': f"Die Bestände kritischer Materialien in {rec.get('department', 'diesem Bereich')} liegen unter dem Optimum. Jetzt nachbestellen, um Engpässe zu vermeiden.",
                            'general': f"Die KI-Analyse der aktuellen Kennzahlen und Trends in {rec.get('department', 'diesem Bereich')} empfiehlt diese Maßnahme zur Optimierung des Betriebs."
                        }
                        explanation = explanations.get(rec_type, explanations['general'])
                    
                    st.markdown(f"""
                    <div style="background: #f9fafb; padding: 1rem; border-radius: 6px; border-left: 3px solid {priority_color};">
                        <div style="color: #4b5563; line-height: 1.6;">{explanation}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Accept/Reject buttons
                col1, col2 = st.columns([3, 1])
                with col1:
                    action_text = st.text_input(
                        "Maßnahme / Begründung",
                        key=f"ops_action_{rec['id']}",
                        placeholder="Bitte ergreifende Maßnahme oder Ablehnungsgrund eingeben"
                    )
                with col2:
                    col_accept, col_reject = st.columns(2)
                    with col_accept:
                        accept_clicked = st.button("✅ Annehmen", key=f"ops_accept_{rec['id']}", use_container_width=True, type="primary")
                        if accept_clicked:
                            if action_text:
                                db.accept_recommendation(rec['id'], action_text)
                                # Apply simulation effect based on recommendation type
                                rec_type = rec.get('rec_type', '')
                                if 'staffing' in rec_type.lower() or 'reassign' in rec.get('action', '').lower():
                                    sim.apply_recommendation_effect(rec_type, 'staffing_reassignment', duration_minutes=30)
                                elif 'capacity' in rec_type.lower() or 'overflow' in rec.get('action', '').lower() or 'bed' in rec.get('action', '').lower():
                                    sim.apply_recommendation_effect(rec_type, 'open_overflow_beds', duration_minutes=45)
                                elif 'room' in rec_type.lower() or 'room' in rec.get('action', '').lower():
                                    sim.apply_recommendation_effect(rec_type, 'room_allocation', duration_minutes=30)
                                st.success("✅ Empfehlung angenommen")
                                st.rerun()
                            else:
                                st.warning("⚠️ Bitte Maßnahme eingeben")
                    with col_reject:
                        reject_clicked = st.button("❌ Ablehnen", key=f"ops_reject_{rec['id']}", use_container_width=True)
                        if reject_clicked:
                            if action_text:
                                db.reject_recommendation(rec['id'], action_text)
                                st.info("❌ Empfehlung abgelehnt")
                                st.rerun()
                            else:
                                st.warning("⚠️ Bitte Ablehnungsgrund eingeben")
                
                st.markdown("---")
        else:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">✅</div>
                <div class="empty-state-title">Keine ausstehenden Empfehlungen</div>
                <div class="empty-state-text">Alle Empfehlungen wurden überprüft</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Audit Tab
    with tab3:
        st.markdown("### Prüfprotokoll")
        st.markdown("")  # Abstand

        # Filter
        audit_log = db.get_audit_log(100)

        col1, col2, col3 = st.columns(3)

        with col1:
            roles = ["Alle"] + sorted(list(set([a.get('user_role', 'system') for a in audit_log if a.get('user_role')])))
            selected_role_audit = st.selectbox("Rolle", roles, key="ops_audit_role")

        with col2:
            actions = ["Alle"] + sorted(list(set([a.get('action_type', '') for a in audit_log if a.get('action_type')])))
            selected_action = st.selectbox("Aktion", actions, key="ops_audit_action")

        with col3:
            areas = ["Alle"] + sorted(list(set([a.get('entity_type', '') for a in audit_log if a.get('entity_type')])))
            selected_area_audit = st.selectbox("Bereich", areas, key="ops_audit_area")

        st.markdown("")  # Abstand
        
        # Apply filters
        filtered_audit = audit_log
        if selected_role_audit != "All":
            filtered_audit = [a for a in filtered_audit if a.get('user_role') == selected_role_audit]
        if selected_action != "All":
            filtered_audit = [a for a in filtered_audit if a.get('action_type') == selected_action]
        if selected_area_audit != "All":
            filtered_audit = [a for a in filtered_audit if a.get('entity_type') == selected_area_audit]
        
        # Display as table
        if filtered_audit:
            # Tabelle mit deutschen Spaltenüberschriften vorbereiten
            table_data = []
            for entry in filtered_audit:
                table_data.append({
                    "Zeit": format_time_ago(entry['timestamp']),
                    "Rolle": entry.get('user_role', 'system').title(),
                    "Aktion": entry['action_type'].replace('_', ' ').title(),
                    "Bereich": entry.get('entity_type', 'N/A'),
                    "Details": entry.get('details', '')[:50] + "..." if entry.get('details') and len(entry.get('details', '')) > 50 else entry.get('details', '')
                })
            
            df_audit = pd.DataFrame(table_data)
            st.dataframe(
                df_audit,
                use_container_width=True,
                hide_index=True,
                height=400
            )

        else:
            st.info("Keine Protokolleinträge gefunden")

elif page == "Live-Metriken":
    st.markdown("### Live-Metriken")
    
    metrics = db.get_recent_metrics(20)
    if metrics:
        df = pd.DataFrame(metrics)
        # German translation for metric types
        metric_type_map = {
            'patient_count': 'Patientenzahl',
            'wait_time': 'Wartezeit',
            'occupancy': 'Auslastung',
            'throughput': 'Durchsatz',
            'waiting_count': 'Wartende Patienten',
            'ed_load': 'Notaufnahme-Auslastung',
            'or_load': 'OP-Auslastung',
            'staff_load': 'Personal-Auslastung',
            'transport_queue': 'Transport-Warteschlange',
            'rooms_free': 'Freie Räume',
            'beds_free': 'Freie Betten',
            # Add more as needed
        }
        # Gruppieren nach Metrik-Typ
        metric_types = df['metric_type'].unique()
        cols = st.columns(3)
        for idx, metric_type in enumerate(metric_types[:6]):
            col_idx = idx % 3
            with cols[col_idx]:
                latest = df[df['metric_type'] == metric_type].iloc[0]
                label = metric_type_map.get(metric_type, metric_type.replace('_', ' ').title())
                # Fix units and formatting for specific metrics
                if metric_type in ['patient_count', 'waiting_count']:
                    unit = ''
                    value_str = f"{int(round(latest['value']))}"
                elif metric_type in ['occupancy', 'ed_load', 'or_load', 'staff_load']:
                    unit = '%'
                    value_str = f"{latest['value']:.1f} {unit}"
                else:
                    unit = latest.get('unit', '')
                    value_str = f"{latest['value']:.1f} {unit}"
                st.metric(
                    label,
                    value_str,
                    delta=None
                )
        # Time series chart
        st.markdown("---")
        st.markdown("### Metrik-Trends")
        # Use German labels in selectbox
        metric_type_labels = [metric_type_map.get(mt, mt.replace('_', ' ').title()) for mt in metric_types]
        metric_type_label_map = dict(zip(metric_type_labels, metric_types))
        selected_label = st.selectbox("Metrik-Typ auswählen", metric_type_labels, key="metric_select")
        selected_metric = metric_type_label_map[selected_label]
        metric_data = df[df['metric_type'] == selected_metric].sort_values('timestamp')
        # German translation for department names
        dept_map = {
            'ER': 'Notaufnahme',
            'ICU': 'Intensivstation',
            'Surgery': 'Chirurgie',
            'General Ward': 'Allgemeinstation',
            'Cardiology': 'Kardiologie',
            'Neurology': 'Neurologie',
            'Pediatrics': 'Pädiatrie',
            'Oncology': 'Onkologie',
            'Orthopedics': 'Orthopädie',
            'Maternity': 'Geburtshilfe',
            'Radiology': 'Radiologie',
            'Other': 'Andere'
        }
        if not metric_data.empty:
            label = metric_type_map.get(selected_metric, selected_metric.replace('_', ' ').title())
            # Map department names to German for plotting and show as 'Abteilung' in legend
            metric_data = metric_data.copy()
            if 'department' in metric_data.columns:
                metric_data['Abteilung'] = metric_data['department'].map(lambda d: dept_map.get(d, d))
                color_col = 'Abteilung'
            else:
                color_col = 'department'
            fig = px.line(
                metric_data,
                x='timestamp',
                y='value',
                color=color_col,
                title=f"{label} Verlauf",
                markers=True
            )
            fig.update_layout(
                height=400,
                xaxis_title="Zeit",
                yaxis_title="Wert",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Keine Metriken verfügbar")

elif page == "Vorhersagen":
    st.markdown("### 5-15 Minuten Vorhersagen")
    
    predictions = db.get_predictions(15)
    if predictions:
        df = pd.DataFrame(predictions)
        # German translation for prediction types
        pred_type_map = {
            'patient_arrival': 'Patientenzugang',
            'bed_demand': 'Bettenbedarf',
            'resource_needed': 'Ressourcenbedarf',
            'waiting_count': 'Wartende Patienten',
            'ed_load': 'Notaufnahme-Auslastung',
            'or_load': 'OP-Auslastung',
            'staff_load': 'Personal-Auslastung',
            'transport_queue': 'Transport-Warteschlange',
            'rooms_free': 'Freie Räume',
            'beds_free': 'Freie Betten',
            # Add more as needed
        }
        dept_map = {
            'ER': 'Notaufnahme',
            'ICU': 'Intensivstation',
            'Surgery': 'Chirurgie',
            'General Ward': 'Allgemeinstation',
            'Cardiology': 'Kardiologie',
            'Neurology': 'Neurologie',
            'Pediatrics': 'Pädiatrie',
            'Oncology': 'Onkologie',
            'Orthopedics': 'Orthopädie',
            'Maternity': 'Geburtshilfe',
            'Radiology': 'Radiologie',
            'Other': 'Andere'
        }
        # Vorhersagen gruppieren
        st.markdown("#### Bevorstehende Vorhersagen")
        for pred in predictions[:10]:
            confidence_color = "#10B981" if pred['confidence'] > 0.8 else "#F59E0B" if pred['confidence'] > 0.7 else "#EF4444"
            # Translate prediction type
            pred_type = pred_type_map.get(pred['prediction_type'], pred['prediction_type'].replace('_', ' ').title())
            # Translate department
            dept = pred.get('department', 'N/A')
            dept_de = dept_map.get(dept, dept)
            # Translate time string
            minutes = pred['time_horizon_minutes']
            if minutes == 1:
                time_str = f'in {minutes} Minute'
            else:
                time_str = f'in {minutes} Minuten'
            st.markdown(f"""
            <div style="background: white; padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>{pred_type}</strong>
                        <div style="color: #6b7280; font-size: 0.875rem; margin-top: 0.25rem;">
                            {dept_de} • {time_str}
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 1.5rem; font-weight: 700; color: #1f2937;">
                            {pred['predicted_value']:.1f}
                        </div>
                        <div style="font-size: 0.75rem; color: {confidence_color};">
                            {pred['confidence']*100:.0f}% Vertrauen
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Prediction chart
        st.markdown("---")
        st.markdown("### Prognose-Vertrauen nach Zeithorizont")
        
        if len(df) > 0:
            # German translation for prediction types
            pred_type_map = {
                'patient_arrival': 'Patientenzugang',
                'bed_demand': 'Bettenbedarf',
                'resource_needed': 'Ressourcenbedarf',
                'waiting_count': 'Wartende Patienten',
                'ed_load': 'Notaufnahme-Auslastung',
                'or_load': 'OP-Auslastung',
                'staff_load': 'Personal-Auslastung',
                'transport_queue': 'Transport-Warteschlange',
                'rooms_free': 'Freie Räume',
                'beds_free': 'Freie Betten',
                # Add more as needed
            }
            df_plot = df.copy()
            df_plot['Problem'] = df_plot['prediction_type'].map(lambda x: pred_type_map.get(x, x.replace('_', ' ').title()))
            fig = px.scatter(
                df_plot,
                x='time_horizon_minutes',
                y='confidence',
                size='predicted_value',
                color='Problem',
                hover_data=['department'],
                title=""
            )
            fig.update_layout(
                height=400,
                xaxis_title="Zeithorizont (Minuten)",
                yaxis_title="Vertrauen",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown(render_empty_state("🔮", "Keine Vorhersagen verfügbar", "Vorhersagen werden hier angezeigt, sobald sie verfügbar sind"), unsafe_allow_html=True)

elif page == "Warnungen":
    alerts = db.get_active_alerts()
    
    if alerts:

        # German translation for severity and departments
        severity_de_map = {'high': 'hoch', 'medium': 'mittel', 'low': 'niedrig'}
        severity_en_map = {v: k for k, v in severity_de_map.items()}
        dept_map = {
            'ER': 'Notaufnahme',
            'ED': 'Notaufnahme',
            'ICU': 'Intensivstation',
            'Surgery': 'Chirurgie',
            'General Ward': 'Allgemeinstation',
            'Cardiology': 'Kardiologie',
            'Neurology': 'Neurologie',
            'Pediatrics': 'Pädiatrie',
            'Oncology': 'Onkologie',
            'Orthopedics': 'Orthopädie',
            'Maternity': 'Geburtshilfe',
            'Radiology': 'Radiologie',
            'Ward': 'Station',
            'Other': 'Andere',
            'N/A': 'Bereich',
        }
        # Build mapping for all unique departments
        unique_depts = sorted(list(set([a.get('department', 'N/A') for a in alerts if a.get('department')])))
        areas_de = [dept_map.get(d, d) for d in unique_depts]
        area_map = dict(zip(areas_de, unique_depts))
        areas_de_display = ["Alle"] + areas_de
        col1, col2 = st.columns(2)
        with col1:
            severity_options = ["Alle", "hoch", "mittel", "niedrig"]
            selected_severity_de = st.selectbox("Schweregrad", severity_options, key="alert_severity")
        with col2:
            selected_area_de = st.selectbox("Bereich", areas_de_display, key="alert_dept")
            selected_area = None if selected_area_de == "Alle" else area_map[selected_area_de]

        filtered_alerts = alerts
        if selected_severity_de != "Alle":
            selected_severity = severity_en_map[selected_severity_de]
            filtered_alerts = [a for a in filtered_alerts if a['severity'] == selected_severity]
        if selected_area is not None:
            filtered_alerts = [a for a in filtered_alerts if a.get('department') == selected_area]
        
        st.markdown("")  # Abstand
        st.markdown("### Aktive Warnungen")
        st.markdown("")  # Abstand
        
        for alert in filtered_alerts:
            severity_color = get_severity_color(alert['severity'])
            severity_de = severity_de_map.get(alert['severity'], alert['severity'])
            badge_html = render_badge(severity_de.upper(), alert['severity'])
            # German translation for alert_type/category
            alert_type_map = {
                'capacity': 'Kapazität',
                'staffing': 'Personal',
                'inventory': 'Inventar',
                'device': 'Gerät',
                'general': 'Allgemein',
                'transport': 'Transport',
                'patient': 'Patient',
                'system': 'System',
                'risk': 'Risiko',
                'other': 'Andere',
            }
            alert_type_de = alert_type_map.get(alert.get('alert_type', 'general'), alert.get('alert_type', 'Allgemein'))
            # Since all alert messages are now in German, just use the message as is
            message_de = alert['message']
            col1, col2 = st.columns([4, 1])
            with col1:
                dept_de = dept_map.get(alert.get('department', 'N/A'), alert.get('department', 'N/A'))
                st.markdown(f"""
                <div style="background: white; padding: 1.25rem; border-radius: 8px; margin-bottom: 0.75rem; border-left: 4px solid {severity_color}; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                    {badge_html}
                    <strong style="margin-left: 0.5rem; color: #1f2937;">{message_de}</strong>
                    <div style="color: #6b7280; font-size: 0.875rem; margin-top: 0.75rem;">
                        {dept_de} • {alert_type_de} • {format_time_ago(alert['timestamp'])}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if st.button("Bestätigen", key=f"ack_{alert['id']}", use_container_width=True):
                    db.acknowledge_alert(alert['id'])
                    st.rerun()
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">✅</div>
            <div class="empty-state-title">Zurzeit keine kritischen Warnungen</div>
            <div class="empty-state-text">Alle Systeme arbeiten normal</div>
        </div>
        """, unsafe_allow_html=True)

elif page == "Empfehlungen":
    st.markdown("### Ausstehende Empfehlungen")
    st.markdown("Überprüfen und Annehmen/Ablehnen von KI-generierten Empfehlungen")
    st.markdown("")  # Abstand
    
    recommendations = db.get_pending_recommendations()
    
    if recommendations:
        for rec in recommendations:
            priority_color = get_priority_color(rec['priority'])
            badge_html = render_badge(rec['priority'].upper(), rec['priority'])
            
            # Get explanation score
            explanation_score = rec.get('explanation_score', 'medium')
            score_color = get_explanation_score_color(explanation_score)
            score_badge = render_badge(f"Vertrauen: {explanation_score.upper()}", explanation_score if explanation_score != 'low' else 'medium')
            
            # Use new template format if available, otherwise fall back to old format
            has_new_format = rec.get('action') and rec.get('reason')
            
            if has_new_format:
                st.markdown(f"""
                <div style="background: white; padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid {priority_color}; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <div style="display: flex; align-items: start; justify-content: space-between; margin-bottom: 1rem;">
                        <div style="flex: 1;">
                            <h4 style="margin: 0 0 0.5rem 0; color: #1f2937;">{rec['title']}</h4>
                            <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 0.75rem;">
                                {badge_html}
                                {score_badge}
                            </div>
                        </div>
                    </div>
                    
                    <div style="background: #f9fafb; padding: 1rem; border-radius: 6px; margin-bottom: 0.75rem;">
                        <div style="margin-bottom: 0.75rem;">
                            <strong style="color: #1f2937; font-size: 0.875rem;">Maßnahme:</strong>
                            <p style="margin: 0.25rem 0 0 0; color: #4b5563; line-height: 1.6;">{rec.get('action', 'N/A')}</p>
                        </div>
                        <div style="margin-bottom: 0.75rem;">
                            <strong style="color: #1f2937; font-size: 0.875rem;">Begründung:</strong>
                            <p style="margin: 0.25rem 0 0 0; color: #4b5563; line-height: 1.6;">{rec.get('reason', 'N/A')}</p>
                        </div>
                        <div style="margin-bottom: 0.75rem;">
                            <strong style="color: #1f2937; font-size: 0.875rem;">Erwartete Auswirkung:</strong>
                            <p style="margin: 0.25rem 0 0 0; color: #4b5563; line-height: 1.6;">{rec.get('expected_impact', 'N/A')}</p>
                        </div>
                        <div>
                            <strong style="color: #1f2937; font-size: 0.875rem;">Sicherheits-Hinweis:</strong>
                            <p style="margin: 0.25rem 0 0 0; color: #4b5563; line-height: 1.6;">{rec.get('safety_note', 'N/A')}</p>
                        </div>
                    </div>
                    
                    <div style="color: #9ca3af; font-size: 0.75rem; margin-top: 0.75rem;">
                        {rec.get('department', 'N/A')} • {rec['rec_type']} • {format_time_ago(rec['timestamp'])}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Fallback to old format
                st.markdown(f"""
                <div style="background: white; padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid {priority_color}; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <div style="display: flex; align-items: start; margin-bottom: 1rem;">
                        {badge_html}
                        <div style="flex: 1;">
                            <h4 style="margin: 0 0 0.5rem 0; color: #1f2937;">{rec['title']}</h4>
                            <p style="color: #6b7280; margin: 0; line-height: 1.6;">{rec['description']}</p>
                            <div style="color: #9ca3af; font-size: 0.75rem; margin-top: 0.5rem;">
                                {rec.get('department', 'N/A')} • {rec['rec_type']} • {format_time_ago(rec['timestamp'])}
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            col1, col2 = st.columns([3, 1])
            with col1:
                action = st.text_input("Maßnahme / Begründung", key=f"action_{rec['id']}", placeholder="Bitte ergreifende Maßnahme oder Ablehnungsgrund eingeben")
            with col2:
                col_accept, col_reject = st.columns(2)
                with col_accept:
                    if st.button("✅ Annehmen", key=f"accept_{rec['id']}", use_container_width=True, type="primary"):
                        if action:
                            db.accept_recommendation(rec['id'], action)
                            # Apply simulation effect based on recommendation type
                            rec_type = rec.get('rec_type', '')
                            if 'staffing' in rec_type.lower() or 'reassign' in rec.get('action', '').lower():
                                sim.apply_recommendation_effect(rec_type, 'staffing_reassignment', duration_minutes=30)
                            elif 'capacity' in rec_type.lower() or 'overflow' in rec.get('action', '').lower() or 'bed' in rec.get('action', '').lower():
                                sim.apply_recommendation_effect(rec_type, 'open_overflow_beds', duration_minutes=45)
                            elif 'room' in rec_type.lower() or 'room' in rec.get('action', '').lower():
                                sim.apply_recommendation_effect(rec_type, 'room_allocation', duration_minutes=30)
                            st.success("✅ Empfehlung angenommen")
                            st.rerun()
                        else:
                            st.warning("⚠️ Bitte Maßnahme eingeben")
                with col_reject:
                    if st.button("❌ Ablehnen", key=f"reject_{rec['id']}", use_container_width=True):
                        if action:
                            db.reject_recommendation(rec['id'], action)
                            st.info("❌ Empfehlung abgelehnt")
                            st.rerun()
                        else:
                            st.warning("⚠️ Bitte Ablehnungsgrund eingeben")
            
            st.markdown("---")
    else:
        st.markdown(render_empty_state("✅", "Keine ausstehenden Empfehlungen", "Alle Empfehlungen wurden überprüft"), unsafe_allow_html=True)

elif page == "Transport":
    st.markdown("### Transport Requests")
    
    transport = db.get_transport_requests()
    
    if transport:
        status_filter = st.selectbox("Nach Status filtern", ["Alle", "Ausstehend", "In Bearbeitung", "Abgeschlossen"], key="transport_status")

        status_map = {
            "Alle": None,
            "Ausstehend": "pending",
            "In Bearbeitung": "in_progress",
            "Abgeschlossen": "completed"
        }
        filtered_transport = transport
        if status_filter != "Alle":
            filtered_transport = [t for t in transport if t['status'] == status_map[status_filter]]

        # Zusammenfassende Kennzahlen
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Ausstehend", len([t for t in transport if t['status'] == 'pending']))
        with col2:
            st.metric("In Bearbeitung", len([t for t in transport if t['status'] == 'in_progress']))
        with col3:
            st.metric("Abgeschlossen", len([t for t in transport if t['status'] == 'completed']))
        with col4:
            avg_time = sum([t['estimated_time_minutes'] or 0 for t in transport]) / len(transport) if transport else 0
            st.metric("Ø geschätzte Zeit", format_duration_minutes(int(avg_time)))

        st.markdown("---")
        
        # Transport table
        for trans in filtered_transport:
            priority_color = get_priority_color(trans['priority'])
            status_color = get_status_color(trans['status'])
            
            st.markdown(f"""
            <div style="background: white; padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span class="badge" style="background: {priority_color}; color: white;">{trans['priority'].upper()}</span>
                        <span class="badge" style="background: {status_color}; color: white; margin-left: 0.5rem;">{trans['status'].replace('_', ' ').upper()}</span>
                        <strong style="margin-left: 0.5rem;">{trans['request_type'].title()}</strong>
                        <div style="color: #6b7280; font-size: 0.875rem; margin-top: 0.25rem;">
                            {trans['from_location']} → {trans['to_location']}
                            {f"• Geschätzt: {format_duration_minutes(trans['estimated_time_minutes'])}" if trans['estimated_time_minutes'] else ""}
                            {f"• Tatsächlich: {format_duration_minutes(trans['actual_time_minutes'])}" if trans['actual_time_minutes'] else ""}
                            • {format_time_ago(trans['timestamp'])}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(render_empty_state("🚑", "Keine Transportanfragen", "Zurzeit keine aktiven Transportanfragen"), unsafe_allow_html=True)

elif page == "Inventar":
    st.markdown("### Bestandsübersicht")
    
    inventory = db.get_inventory_status()
    
    if inventory:
        # Warnung bei niedrigem Bestand
        low_stock = [i for i in inventory if i['current_stock'] < i['min_threshold']]
        if low_stock:
            st.warning(f"⚠️ {len(low_stock)} Artikel unter Mindestbestand")
        
        # Inventory cards
        cols = st.columns(3)
        for idx, item in enumerate(inventory):
            col_idx = idx % 3
            with cols[col_idx]:
                status = calculate_inventory_status(item['current_stock'], item['min_threshold'], item['max_capacity'])
                status_color = get_severity_color(status['status']) if status['status'] != 'normal' else "#10B981"
                
                st.markdown(f"""
                <div style="background: white; padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid {status_color};">
                    <div style="font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.05em;">
                        {item['category']}
                    </div>
                    <div style="font-size: 1.25rem; font-weight: 700; color: #1f2937; margin: 0.5rem 0;">
                        {item['item_name']}
                    </div>
                    <div style="font-size: 2rem; font-weight: 700; color: {status_color}; margin: 0.5rem 0;">
                        {item['current_stock']} <span style="font-size: 0.875rem; color: #6b7280;">{item['unit']}</span>
                    </div>
                    <div style="font-size: 0.75rem; color: #9ca3af; margin-top: 0.5rem;">
                        Mindestbestand: {item['min_threshold']} • Kapazität: {item['max_capacity']}
                    </div>
                    <div style="margin-top: 0.5rem;">
                        <div style="background: #e5e7eb; height: 4px; border-radius: 2px; overflow: hidden;">
                            <div style="background: {status_color}; height: 100%; width: {status['percentage']}%;"></div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # Chart
        st.markdown("---")
        st.markdown("### Bestandsverlauf")
        df_inv = pd.DataFrame(inventory)
        df_inv['utilization'] = (df_inv['current_stock'] / df_inv['max_capacity']) * 100
        
        fig = px.bar(
            df_inv,
            x='item_name',
            y='utilization',
            color='department',
            title="Bestandsauslastung nach Artikel",
            labels={'utilization': 'Auslastung %', 'item_name': 'Artikel'}
        )
        fig.update_layout(
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Keine Bestandsdaten verfügbar")

elif page == "Gerätewartung":
    st.markdown("### Gerätewartungs-Risikoanalyse")
    
    devices = db.get_device_maintenance_risks()
    
    if devices:
        # Risikozusammenfassung
        high_risk = len([d for d in devices if d['risk_level'] == 'high'])
        medium_risk = len([d for d in devices if d['risk_level'] == 'medium'])

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Geräte mit hohem Risiko", high_risk, delta=None)
        with col2:
            st.metric("Geräte mit mittlerem Risiko", medium_risk, delta=None)
        with col3:
            st.metric("Gesamtanzahl Geräte", len(devices))

        st.markdown("---")
        
        # Device cards
        for device in devices:
            risk_color = get_risk_color(device['risk_level'])
            status_color = get_status_color(device['status'])
            
            # German translation for device card labels
            risk_label = {
                'high': 'HOHES RISIKO',
                'medium': 'MITTLERES RISIKO',
                'low': 'GERINGES RISIKO'
            }.get(device['risk_level'], device['risk_level'].upper())
            status_label = {
                'active': 'AKTIV',
                'inactive': 'INAKTIV',
                'maintenance': 'IN WARTUNG',
                'pending': 'AUSSTEHEND',
                'in_use': 'IN BENUTZUNG',
                'available': 'VERFÜGBAR',
                'unavailable': 'NICHT VERFÜGBAR',
                'in_progress': 'IN BEARBEITUNG',
                'completed': 'ABGESCHLOSSEN'
            }.get(device['status'], device['status'].upper())
            
            st.markdown(f"""
            <div style="background: white; padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid {risk_color};">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div style="flex: 1;">
                        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                            <span class="badge" style="background: {risk_color}; color: white;">{risk_label}</span>
                            <span class="badge" style="background: {status_color}; color: white;">{status_label}</span>
                        </div>
                        <h4 style="margin: 0 0 0.5rem 0;">{device['device_type']} - {device['device_id']}</h4>
                        <div style="color: #6b7280; font-size: 0.875rem;">
                            <div>Abteilung: {device.get('department', 'N/V')}</div>
                            <div>Nutzungsdauer: {device['usage_hours']} Stunden</div>
                            <div>Letzte Wartung: {device['last_maintenance']}</div>
                            <div>Nächste fällig: {device['next_maintenance_due']}</div>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Risk distribution chart
        st.markdown("---")
        st.markdown("### Risikoverteilung")
        df_dev = pd.DataFrame(devices)
        risk_counts = df_dev['risk_level'].value_counts()
        
        fig = px.pie(
            values=risk_counts.values,
            names=risk_counts.index,
            color=risk_counts.index,
            color_discrete_map={
                'high': '#DC2626',
                'medium': '#F59E0B',
                'low': '#10B981'
            }
        )
        fig.update_layout(
            height=300,
            showlegend=True,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown(render_empty_state("🔧", "Keine Gerätedaten verfügbar", "Gerätewartungsdaten werden hier angezeigt, sobald sie verfügbar sind"), unsafe_allow_html=True)

elif page == "Entlassungsplanung":
    st.markdown("### Entlassungsplanungs-Übersicht")
    st.markdown("Aggregierte Entlassungsmetriken nach Abteilung")
    
    discharge = db.get_discharge_planning()
    
    if discharge:
        df_disch = pd.DataFrame(discharge)
        # Rename columns for German legend/axis
        df_disch = df_disch.rename(columns={
            'ready_for_discharge_count': 'Entlassungsbereit',
            'pending_discharge_count': 'Ausstehend'
        })

        # Summary metrics
        total_ready = df_disch['Entlassungsbereit'].sum()
        total_pending = df_disch['Ausstehend'].sum()
        avg_los = df_disch['avg_length_of_stay_hours'].mean()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Entlassungsbereit", total_ready)
        with col2:
            st.metric("Ausstehende Entlassungen", total_pending)
        with col3:
            st.metric("Ø Verweildauer", f"{avg_los:.1f} Stunden")
        
        st.markdown("---")
        
        # Department cards
        cols = st.columns(3)
        for idx, dept_data in enumerate(discharge):
            col_idx = idx % 3
            with cols[col_idx]:
                dept_color = get_department_color(dept_data['department'])
                # Use German keys if present, else fallback to English for backward compatibility
                ready = dept_data.get('Entlassungsbereit', dept_data.get('ready_for_discharge_count', 0))
                pending = dept_data.get('Ausstehend', dept_data.get('pending_discharge_count', 0))
                avg_los = dept_data.get('avg_length_of_stay_hours', 0)
                st.markdown(f"""
                <div style="background: white; padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem; border-top: 4px solid {dept_color};">
                    <h4 style="margin: 0 0 1rem 0; color: {dept_color};">{dept_data['department']}</h4>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                        <span style="color: #6b7280;">Entlassungsbereit:</span>
                        <strong>{ready}</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                        <span style="color: #6b7280;">Ausstehend:</span>
                        <strong>{pending}</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                        <span style="color: #6b7280;">Ø Verweildauer:</span>
                        <strong>{avg_los:.1f}h</strong>
                    </div>
                    <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #e5e7eb;">
                        <div style="font-size: 0.75rem; color: #9ca3af; margin-bottom: 0.25rem;">Kapazitätsauslastung</div>
                        <div style="background: #e5e7eb; height: 8px; border-radius: 4px; overflow: hidden;">
                            <div style="background: {dept_color}; height: 100%; width: {dept_data['discharge_capacity_utilization']*100}%;"></div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # Charts
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(
                df_disch,
                x='department',
                y=['Entlassungsbereit', 'Ausstehend'],
                title="Entlassungsstatus nach Abteilung",
                barmode='group',
                color_discrete_map={'Entlassungsbereit': '#10B981', 'Ausstehend': '#F59E0B'},
                labels={
                    'department': 'Abteilung',
                    'Entlassungsbereit': 'Entlassungsbereit',
                    'Ausstehend': 'Ausstehend'
                }
            )
            fig.update_layout(
                height=300,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Mapping for department names (English to German)
            department_map = {
                'ER': 'Notaufnahme',
                'ICU': 'Intensivstation',
                'Surgery': 'Chirurgie',
                'General Ward': 'Allgemeinstation',
                'Cardiology': 'Kardiologie',
                'Neurology': 'Neurologie',
                'Pediatrics': 'Pädiatrie',
                'Oncology': 'Onkologie',
                'Orthopedics': 'Orthopädie',
                'Maternity': 'Geburtshilfe',
                'Radiology': 'Radiologie',
                'Other': 'Andere'
            }
            # Add German department column for plotting
            df_disch['Abteilung'] = df_disch['department'].map(department_map).fillna(df_disch['department'])
            fig = px.bar(
                df_disch,
                x='Abteilung',
                y='avg_length_of_stay_hours',
                title="Ø Verweildauer nach Abteilung",
                color='Abteilung',
                color_discrete_map={department_map.get(dept, dept): get_department_color(dept) for dept in df_disch['department']},
                labels={
                    'Abteilung': 'Abteilung',
                    'avg_length_of_stay_hours': 'Ø Verweildauer (Std.)'
                }
            )
            fig.update_layout(
                height=300,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown(render_empty_state("🏥", "Keine Entlassungsplanungsdaten", "Entlassungsplanungsdaten werden hier angezeigt, sobald sie verfügbar sind"), unsafe_allow_html=True)

elif page == "Entlassung":
    # Erwartete Entlassungen simulieren
    jetzt = datetime.now()

    # Erwartete Entlassungen für die nächsten 12 Stunden (stündliche Intervalle) generieren
    stündliche_entlassungen = []
    for stunde in range(12):
        stundenzeit = jetzt + timedelta(hours=stunde)
        # Entlassungszahlen simulieren (morgens/nachmittags höher, nachts niedriger)
        if 8 <= stunde < 12:  # Morgenpeak
            anzahl = random.randint(3, 8)
        elif 12 <= stunde < 18:  # Nachmittagspeak
            anzahl = random.randint(2, 6)
        elif 18 <= stunde < 22:  # Abend
            anzahl = random.randint(1, 4)
        else:  # Nacht
            anzahl = random.randint(0, 2)

        stündliche_entlassungen.append({
            'stunde': stundenzeit,
            'stunden_label': stundenzeit.strftime('%H:00'),
            'anzahl': anzahl
        })

    # Erwartete Entlassungen in den nächsten 4 Stunden berechnen
    nächste_4h_entlassungen = sum([d['anzahl'] for d in stündliche_entlassungen[:4]])

    # Große Kennzahl für die nächsten 4 Stunden
    st.markdown("### Erwartete Entlassungen")
    st.markdown("")  # Abstand

    spalte1, spalte2, spalte3 = st.columns([2, 1, 1])
    with spalte1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
            <div style="color: white; font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem; opacity: 0.9;">
                Erwartete Entlassungen in den nächsten 4 Stunden
            </div>
            <div style="color: white; font-size: 4rem; font-weight: 700; line-height: 1;">
                {nächste_4h_entlassungen}
            </div>
            <div style="color: white; font-size: 1rem; margin-top: 0.5rem; opacity: 0.9;">
                Aggregierte Anzahl
            </div>
        </div>
        """, unsafe_allow_html=True)

    with spalte2:
        nächste_8h_entlassungen = sum([d['anzahl'] for d in stündliche_entlassungen[:8]])
        st.metric("Nächste 8 Stunden", nächste_8h_entlassungen, delta=None)

    with spalte3:
        nächste_12h_entlassungen = sum([d['anzahl'] for d in stündliche_entlassungen])
        st.metric("Nächste 12 Stunden", nächste_12h_entlassungen, delta=None)

    st.markdown("---")

    # Zeitstrahl für die nächsten 12 Stunden
    st.markdown("### Entlassungs-Zeitstrahl (Nächste 12 Stunden)")
    st.markdown("")  # Abstand

    df_zeitstrahl = pd.DataFrame(stündliche_entlassungen)

    fig_zeitstrahl = px.bar(
        df_zeitstrahl,
        x='stunden_label',
        y='anzahl',
        title="",
        labels={'stunden_label': 'Zeit', 'anzahl': 'Erwartete Entlassungen'},
        color='anzahl',
        color_continuous_scale='Blues'
    )
    fig_zeitstrahl.update_layout(
        height=400,
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis_title="",
        yaxis_title="Erwartete Entlassungen",
        showlegend=False,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='#e5e7eb', showline=False)
    )
    fig_zeitstrahl.update_traces(marker_line_width=0)
    st.plotly_chart(fig_zeitstrahl, use_container_width=True)

    st.markdown("---")

    # Empfehlungen
    st.markdown("### Empfehlungen")
    st.markdown("")  # Abstand

    # Empfehlungen basierend auf Entlassungsmustern simulieren
    empfehlungen = []

    # Prüfe auf Fälle, die eine frühere Entlassungsplanung benötigen
    hohe_entlassungsstunden = [d for d in stündliche_entlassungen[:6] if d['anzahl'] >= 5]
    if hohe_entlassungsstunden:
        gesamt_hoch = sum([d['anzahl'] for d in hohe_entlassungsstunden])
        empfehlungen.append({
            "type": "early_planning",
            "message": f"Frühzeitige Entlassungsplanung für {gesamt_hoch} Fälle (gesamt) starten",
            "details": f"Hohes Entlassungsaufkommen in den nächsten 6 Stunden erwartet. Frühzeitige Planung kann Verzögerungen um 20-30% reduzieren.",
            "priority": "mittel"
        })

    # Prüfe auf potenzielle Engpässe
    spitzenstunde = max(stündliche_entlassungen[:8], key=lambda x: x['anzahl'])
    if spitzenstunde['anzahl'] >= 6:
        empfehlungen.append({
            "type": "resource_allocation",
            "message": f"Zusätzliche Ressourcen für {spitzenstunde['stunden_label']} bereitstellen (erwartet {spitzenstunde['anzahl']} Entlassungen)",
            "details": f"Spitzenzeit für Entlassungen erkannt. Zusätzliche Mitarbeitende oder Transportkapazität einplanen.",
            "priority": "hoch"
        })

    # Prüfe auf niedrige Entlassungsphasen (Aufholpotenzial)
    niedrige_entlassungsstunden = [d for d in stündliche_entlassungen if d['anzahl'] <= 1]
    if len(niedrige_entlassungsstunden) >= 3:
        empfehlungen.append({
            "type": "catch_up",
            "message": f"Niedrigphasen für Aufholarbeiten nutzen (mind. 3 Stunden mit ≤1 erwarteter Entlassung)",
            "details": "Mehrere Niedrigphasen erkannt. Gute Gelegenheit, ausstehende Entlassungen zu bearbeiten.",
            "priority": "niedrig"
        })

    if empfehlungen:
        for emp in empfehlungen:
            priority_color = get_priority_color(emp['priority'])
            badge_html = render_badge(emp['priority'].upper(), emp['priority'])

            st.markdown(f"""
            <div style="background: white; padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid {priority_color}; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <div style="display: flex; align-items: start; gap: 0.75rem; margin-bottom: 0.75rem;">
                    {badge_html}
                    <div style="flex: 1;">
                        <h4 style="margin: 0 0 0.5rem 0; color: #1f2937;">{emp['message']}</h4>
                        <p style="color: #6b7280; margin: 0; line-height: 1.6;">{emp['details']}</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(render_empty_state("💡", "Keine Empfehlungen zum aktuellen Zeitpunkt", "Alle Systeme arbeiten im normalen Bereich"), unsafe_allow_html=True)

    # Weitere aggregierte Statistiken
    st.markdown("---")
    st.markdown("### Statistiken")
    st.markdown("")  # Abstand

    spalte1, spalte2, spalte3, spalte4 = st.columns(4)

    with spalte1:
        spitzenstunde = max(stündliche_entlassungen, key=lambda x: x['anzahl'])
        st.metric("Spitzenstunde", spitzenstunde['stunden_label'], delta=f"{spitzenstunde['anzahl']} Entlassungen")

    with spalte2:
        durchschnitt_pro_stunde = sum([d['anzahl'] for d in stündliche_entlassungen]) / len(stündliche_entlassungen)
        st.metric("Durchschnitt pro Stunde", f"{durchschnitt_pro_stunde:.1f}", delta=None)

    with spalte3:
        gesamt_12h = sum([d['anzahl'] for d in stündliche_entlassungen])
        st.metric("Gesamt (12h)", gesamt_12h, delta=None)

    with spalte4:
        niedrige_stunden = len([d for d in stündliche_entlassungen if d['anzahl'] <= 1])
        st.metric("Stunden mit niedriger Aktivität", niedrige_stunden, delta=None)

elif page == "Kapazitätsübersicht":
    st.markdown("### Kapazitätsübersicht")
    
    capacity = db.get_capacity_overview()
    
    if capacity:
        df_cap = pd.DataFrame(capacity)
        
        # Gesamte Kennzahlen
        gesamt_betten = df_cap['total_beds'].sum()
        belegte_betten = df_cap['occupied_beds'].sum()
        verfügbare_betten = df_cap['available_beds'].sum()
        gesamt_auslastung = belegte_betten / gesamt_betten if gesamt_betten > 0 else 0

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Gesamtbetten", gesamt_betten)
        with col2:
            st.metric("Belegt", belegte_betten)
        with col3:
            st.metric("Verfügbar", verfügbare_betten)
        with col4:
            kapazitäts_status = calculate_capacity_status(gesamt_auslastung)
            st.metric("Gesamtauslastung", f"{kapazitäts_status['percentage']}%")

        st.markdown("---")
        
        # Department capacity cards
        # Mapping for department names (English to German)
        department_map = {
            'ER': 'Notaufnahme',
            'ICU': 'Intensivstation',
            'Surgery': 'Chirurgie',
            'General Ward': 'Allgemeinstation',
            'Cardiology': 'Kardiologie',
            'Neurology': 'Neurologie',
            'Pediatrics': 'Pädiatrie',
            'Oncology': 'Onkologie',
            'Orthopedics': 'Orthopädie',
            'Maternity': 'Geburtshilfe',
            'Radiology': 'Radiologie',
            'Other': 'Andere'
        }
        for cap in capacity:
            cap_status = calculate_capacity_status(cap['utilization_rate'])
            dept_color = get_department_color(cap['department'])
            # Use German department name if available
            german_dept = department_map.get(cap['department'], cap['department'])
            
            st.markdown(f"""
            <div style="background: white; padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid {cap_status['color']};">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h4 style="margin: 0; color: {dept_color};">{german_dept}</h4>
                    <span class="badge" style="background: {cap_status['color']}; color: white;">{cap_status['status'].upper()}</span>
                </div>
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 1rem;">
                    <div>
                        <div style="font-size: 0.75rem; color: #6b7280; text-transform: uppercase;">Gesamt</div>
                        <div style="font-size: 1.5rem; font-weight: 700; color: #1f2937;">{cap['total_beds']}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.75rem; color: #6b7280; text-transform: uppercase;">Belegt</div>
                        <div style="font-size: 1.5rem; font-weight: 700; color: #DC2626;">{cap['occupied_beds']}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.75rem; color: #6b7280; text-transform: uppercase;">Verfügbar</div>
                        <div style="font-size: 1.5rem; font-weight: 700; color: #10B981;">{cap['available_beds']}</div>
                    </div>
                </div>
                <div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                        <span style="font-size: 0.875rem; color: #6b7280;">Auslastung</span>
                        <span style="font-weight: 600; color: {cap_status['color']};">{cap_status['percentage']}%</span>
                    </div>
                    <div style="background: #e5e7eb; height: 12px; border-radius: 6px; overflow: hidden;">
                        <div style="background: {cap_status['color']}; height: 100%; width: {cap_status['percentage']}%;"></div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
       # Capacity charts
        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            # Mapping for department names (English to German)
            department_map = {
                'ER': 'Notaufnahme',
                'ICU': 'Intensivstation',
                'Surgery': 'Chirurgie',
                'General Ward': 'Allgemeinstation',
                'Cardiology': 'Kardiologie',
                'Neurology': 'Neurologie',
                'Pediatrics': 'Pädiatrie',
                'Oncology': 'Onkologie',
                'Orthopedics': 'Orthopädie',
                'Maternity': 'Geburtshilfe',
                'Radiology': 'Radiologie',
                'Other': 'Andere'
            }
            # Add German department column for plotting
            df_cap['Abteilung'] = df_cap['department'].map(department_map).fillna(df_cap['department'])
            color_map = {department_map.get(dept, dept): get_department_color(dept) for dept in df_cap['department']}
            fig = px.bar(
                df_cap,
                x='Abteilung',
                y='utilization_rate',
                title="Auslastung nach Abteilung",
                color='Abteilung',
                color_discrete_map=color_map,
                labels={'utilization_rate': 'Auslastung (%)', 'Abteilung': 'Abteilung'}
            )
            fig.update_layout(
                height=400,
                yaxis=dict(
                    tickformat='.0%',
                    title='Auslastung (%)'
                ),
                xaxis=dict(title='Abteilung'),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = go.Figure(data=[
                go.Bar(name='Belegt', x=df_cap['Abteilung'], y=df_cap['occupied_beds'], marker_color='#DC2626'),
                go.Bar(name='Verfügbar', x=df_cap['Abteilung'], y=df_cap['available_beds'], marker_color='#10B981')
            ])
            fig.update_layout(
                title="Bettenverfügbarkeit nach Abteilung",
                height=400,
                barmode='stack',
                xaxis_title="Abteilung",
                yaxis_title="Betten",
                legend_title_text="Status",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown(render_empty_state("📋", "Keine Kapazitätsdaten verfügbar", "Kapazitätsdaten werden hier angezeigt, sobald sie verfügbar sind"), unsafe_allow_html=True)

elif page == "Prüfprotokoll":
    st.markdown("### Prüfprotokoll")
    st.markdown("Alle Systemaktionen und Änderungen verfolgen")
    
    audit_log = db.get_audit_log(100)
    
    if audit_log:
        # Filteroptionen
        col1, col2 = st.columns(2)
        with col1:
            action_filter = st.selectbox(
                "Nach Aktion filtern",
                ["Alle"] + list(set([a['action_type'] for a in audit_log])),
                key="audit_action"
            )
        with col2:
            limit = st.slider("Anzahl der Einträge", 10, 100, 50, key="audit_limit")
        
        filtered_log = audit_log[:limit]
        if action_filter != "Alle":
            filtered_log = [a for a in filtered_log if a['action_type'] == action_filter]
        
        # Audit-Log-Tabelle
        st.markdown("---")
        for entry in filtered_log:
            st.markdown(f"""
            <div style="background: white; padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem; border-left: 3px solid #667eea;">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div style="flex: 1;">
                        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                            <span style="font-weight: 600; color: #1f2937;">{entry['action_type'].replace('_', ' ').title()}</span>
                            {f"<span style='color: #6b7280; font-size: 0.875rem;'>({entry['entity_type']} #{entry['entity_id']})</span>" if entry['entity_id'] else ""}
                        </div>
                        {f"<div style='color: #6b7280; font-size: 0.875rem;'>{entry['details']}</div>" if entry['details'] else ""}
                        <div style="color: #9ca3af; font-size: 0.75rem; margin-top: 0.5rem;">
                            {entry.get('user_role', 'system').title()} • {format_time_ago(entry['timestamp'])}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(render_empty_state("📝", "Keine Prüfprotokoll-Einträge", "Prüfprotokoll-Einträge werden hier angezeigt, sobald sie verfügbar sind"), unsafe_allow_html=True)

elif page == "Vermögenswerte":
    # Abschnitt Lager-/Inventarrisiko
    st.markdown("### Lagerrisiko")
    st.markdown("")  # Abstand
    
    # Simulierte Inventarmaterialien mit Risiko
    inventory_materials = [
        {"name": "Untersuchungshandschuhe (Nitril)", "current_stock": 45, "min_threshold": 100, "max_capacity": 500, "unit": "Boxen", "department": "Chirurgie", "days_until_stockout": 3},
        {"name": "IV-Katheter (18G)", "current_stock": 12, "min_threshold": 50, "max_capacity": 300, "unit": "Stück", "department": "Notaufnahme", "days_until_stockout": 2},
        {"name": "Antibiotika-Lösung (Ceftriaxon)", "current_stock": 8, "min_threshold": 30, "max_capacity": 200, "unit": "Fläschchen", "department": "Intensivstation", "days_until_stockout": 1},
        {"name": "Sauerstoffmasken (Erwachsene)", "current_stock": 25, "min_threshold": 40, "max_capacity": 150, "unit": "Stück", "department": "Allgemeinstation", "days_until_stockout": 5},
        {"name": "Defibrillator-Pads", "current_stock": 6, "min_threshold": 20, "max_capacity": 100, "unit": "Paare", "department": "Kardiologie", "days_until_stockout": 1},
    ]
    
    # Calculate risk for each material
    for material in inventory_materials:
        stock_percent = (material['current_stock'] / material['max_capacity']) * 100
        threshold_percent = (material['min_threshold'] / material['max_capacity']) * 100

        # Risiko auf Deutsch zuweisen
        if material['current_stock'] < material['min_threshold']:
            if material['days_until_stockout'] <= 2:
                risk_level = "hoch"
            else:
                risk_level = "mittel"
        else:
            risk_level = "niedrig"

        material['risk_level'] = risk_level
        material['stock_percent'] = stock_percent
        material['threshold_percent'] = threshold_percent

    # Nach Risiko sortieren (hoch zuerst)
    inventory_materials.sort(key=lambda x: {'hoch': 1, 'mittel': 2, 'niedrig': 3}[x['risk_level']])
    top_5_materials = inventory_materials[:5]

    # Anzeige der Top-5-Risiko-Materialien
    if top_5_materials:
        table_data = []
        for mat in top_5_materials:
            risk_color = get_severity_color(mat['risk_level'])
            risk_badge = render_badge(mat['risk_level'].upper(), mat['risk_level'])
            table_data.append({
                "Material": mat['name'],
                "Aktueller Bestand": f"{mat['current_stock']} {mat['unit']}",
                "Mindestbestand": f"{mat['min_threshold']} {mat['unit']}",
                "Tage bis Engpass": mat['days_until_stockout'],
                "Risiko": risk_badge,
                "Abteilung": mat['department']
            })
        
        df_inv = pd.DataFrame(table_data)
        # Risiko-Spalte als HTML anzeigen
        st.markdown("#### Top 5 Materialien mit Risiko")
        st.markdown("")  # Abstand
        
        # Display as styled table
        for mat in top_5_materials:
            risk_color = get_severity_color(mat['risk_level'])
            risk_badge = render_badge(mat['risk_level'].upper(), mat['risk_level'])
            st.markdown(f"""
            <div style="background: white; padding: 1rem; border-radius: 8px; margin-bottom: 0.75rem; border-left: 4px solid {risk_color}; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                <div style="display: grid; grid-template-columns: 2fr 1fr 1fr 1fr 1fr; gap: 1rem; align-items: center;">
                    <div>
                        <div style="font-weight: 600; color: #1f2937; margin-bottom: 0.25rem;">{mat['name']}</div>
                        <div style="font-size: 0.75rem; color: #6b7280;">{mat['department']}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.75rem; color: #6b7280; margin-bottom: 0.25rem;">Aktuell</div>
                        <div style="font-weight: 600; color: #1f2937;">{mat['current_stock']} {mat['unit']}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.75rem; color: #6b7280; margin-bottom: 0.25rem;">Mindestbestand</div>
                        <div style="font-weight: 600; color: #1f2937;">{mat['min_threshold']} {mat['unit']}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.75rem; color: #6b7280; margin-bottom: 0.25rem;">Tage bis Engpass</div>
                        <div style="font-weight: 600; color: {risk_color};">{mat['days_until_stockout']} Tage</div>
                    </div>
                    <div>
                        {risk_badge}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Nachfüllvorschläge
    st.markdown("---")
    st.markdown("#### Nachfüllvorschläge")
    st.markdown("")  # Abstand
    
    restock_suggestions = []
    for mat in top_5_materials:
        if mat['risk_level'] in ['high', 'medium']:
            suggested_qty = max(mat['min_threshold'] * 2, mat['min_threshold'] + 50)
            restock_suggestions.append({
                "material": mat['name'],
                "suggested_qty": suggested_qty,
                "current": mat['current_stock'],
                "priority": mat['risk_level']
            })
    
    if restock_suggestions:
        for suggestion in restock_suggestions:
            priority_color = get_severity_color(suggestion['priority'])
            st.markdown(f"""
            <div style="background: #f9fafb; padding: 1rem; border-radius: 6px; margin-bottom: 0.5rem; border-left: 3px solid {priority_color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-weight: 600; color: #1f2937;">{suggestion['material']}</div>
                        <div style="font-size: 0.875rem; color: #6b7280; margin-top: 0.25rem;">
                            Aktuell: {suggestion['current']} → Vorgeschlagen: {suggestion['suggested_qty']} Einheiten
                        </div>
                    </div>
                    <div style="font-weight: 600; color: {priority_color};">
                        +{suggestion['suggested_qty'] - suggestion['current']} Einheiten
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(render_empty_state("📦", "Keine Nachfüllvorschläge", "Alle Lagerbestände sind ausreichend"), unsafe_allow_html=True)
    
    # Risikoverteilung
    st.markdown("---")
    st.markdown("#### Risikoverteilung")
    st.markdown("")  # Abstand

    # Deutsche Risikostufen
    risk_counts = {'hoch': 0, 'mittel': 0, 'niedrig': 0}
    for mat in inventory_materials:
        risk_counts[mat['risk_level']] = risk_counts.get(mat['risk_level'], 0) + 1

    risikostufen_labels = {"hoch": "Hoch", "mittel": "Mittel", "niedrig": "Niedrig"}
    risikostufen_farben = {"hoch": '#DC2626', "mittel": '#F59E0B', "niedrig": '#10B981'}

    fig_risk = px.bar(
        x=[risikostufen_labels[k] for k in risk_counts.keys()],
        y=list(risk_counts.values()),
        title="",
        labels={'x': 'Risikostufe', 'y': 'Anzahl'},
        color=[risikostufen_labels[k] for k in risk_counts.keys()],
        color_discrete_map={risikostufen_labels[k]: risikostufen_farben[k] for k in risk_counts.keys()}
    )
    fig_risk.update_layout(
        height=300,
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        xaxis_title="Risikostufe",
        yaxis_title="Anzahl Materialien"
    )
    st.plotly_chart(fig_risk, use_container_width=True)
    
    st.markdown("---")
    
    # Gerätrisiko-Abschnitt
    st.markdown("### Gerätrisiko")
    st.markdown("")  # Abstand
    
    # Simulated devices with risk
    devices = [
        {"name": "MRI Scanner", "device_id": "MRI-001", "type": "Imaging", "department": "Radiology", "risk_level": "high", "last_maintenance": "2024-01-15", "next_maintenance_due": "2024-02-15", "days_until_due": 5, "usage_hours": 3200, "recommended_window": "Within 3 days"},
        {"name": "CT Scanner", "device_id": "CT-203", "type": "Imaging", "department": "Radiology", "risk_level": "medium", "last_maintenance": "2024-01-20", "next_maintenance_due": "2024-03-20", "days_until_due": 18, "usage_hours": 2400, "recommended_window": "Within 2 weeks"},
        {"name": "X-Ray Machine", "device_id": "XR-501", "type": "Imaging", "department": "ER", "risk_level": "low", "last_maintenance": "2024-02-01", "next_maintenance_due": "2024-05-01", "days_until_due": 45, "usage_hours": 1800, "recommended_window": "Within 4 weeks"},
        {"name": "Ultrasound System", "device_id": "US-102", "type": "Imaging", "department": "Cardiology", "risk_level": "medium", "last_maintenance": "2024-01-25", "next_maintenance_due": "2024-03-25", "days_until_due": 23, "usage_hours": 2100, "recommended_window": "Within 2 weeks"},
        {"name": "Ventilator", "device_id": "V-203", "type": "Life Support", "department": "ICU", "risk_level": "high", "last_maintenance": "2024-01-15", "next_maintenance_due": "2024-02-15", "days_until_due": 5, "usage_hours": 3200, "recommended_window": "Within 3 days"},
        {"name": "Defibrillator", "device_id": "D-102", "type": "Emergency", "department": "Cardiology", "risk_level": "low", "last_maintenance": "2024-02-01", "next_maintenance_due": "2024-05-01", "days_until_due": 45, "usage_hours": 1800, "recommended_window": "Within 4 weeks"},
    ]
    
    # Display devices table
    st.markdown("#### Gerätewartungsstatus")
    st.markdown("")  # Abstand
    
    # Mapping for device types to German
    device_type_map = {
        'Imaging': 'Bildgebung',
        'Life Support': 'Lebensunterstützung',
        'Emergency': 'Notfall',
        'Monitoring': 'Überwachung',
        'Therapy': 'Therapie',
        'Surgical': 'Chirurgisch',
        'Diagnostic': 'Diagnostik',
        'Other': 'Andere',
    }
    # Mapping for risk levels to German
    risk_level_map = {'high': 'hoch', 'medium': 'mittel', 'low': 'niedrig', 'hoch': 'hoch', 'mittel': 'mittel', 'niedrig': 'niedrig'}
    risk_label_map = {'hoch': 'HOHES RISIKO', 'mittel': 'MITTLERES RISIKO', 'niedrig': 'GERINGES RISIKO'}
    for device in devices:
        risk_level_de = risk_level_map.get(device['risk_level'], device['risk_level'])
        risk_color = get_severity_color(risk_level_de)
        risk_badge = render_badge(risk_label_map.get(risk_level_de, risk_level_de.upper()), risk_level_de)
        device_type_de = device_type_map.get(device['type'], device['type'])
        # Mapping for recommended_window to German
        recommended_window_map = {
            'Within 3 days': 'Innerhalb von 3 Tagen',
            'Within 2 weeks': 'Innerhalb von 2 Wochen',
            'Within 4 weeks': 'Innerhalb von 4 Wochen',
            'Within 1 week': 'Innerhalb von 1 Woche',
            'Overdue': 'Überfällig',
            'Soon': 'Bald',
        }
        recommended_window_de = recommended_window_map.get(device.get('recommended_window', ''), device.get('recommended_window', ''))
        # Mapping for department names to German
        department_map = {
            'Radiology': 'Radiologie',
            'ER': 'Notaufnahme',
            'ICU': 'Intensivstation',
            'Cardiology': 'Kardiologie',
            'Surgery': 'Chirurgie',
            'General Ward': 'Allgemeinstation',
            'Neurology': 'Neurologie',
            'Pediatrics': 'Pädiatrie',
            'Oncology': 'Onkologie',
            'Orthopedics': 'Orthopädie',
            'Maternity': 'Geburtshilfe',
            'Other': 'Andere',
        }
        department_de = department_map.get(device.get('department', ''), device.get('department', ''))
        st.markdown(f"""
        <div style="background: white; padding: 1rem; border-radius: 8px; margin-bottom: 0.75rem; border-left: 4px solid {risk_color}; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
            <div style="display: grid; grid-template-columns: 2fr 1fr 1fr 1fr 1fr 1fr; gap: 1rem; align-items: center;">
                <div>
                    <div style="font-weight: 600; color: #1f2937; margin-bottom: 0.25rem;">{device['name']}</div>
                    <div style="font-size: 0.75rem; color: #6b7280;">{device['device_id']} • {department_de}</div>
                </div>
                <div>
                    <div style="font-size: 0.75rem; color: #6b7280; margin-bottom: 0.25rem;">Gerätetyp</div>
                    <div style="font-weight: 600; color: #1f2937;">{device_type_de}</div>
                </div>
                <div>
                    <div style="font-size: 0.75rem; color: #6b7280; margin-bottom: 0.25rem;">Tage bis fällig</div>
                    <div style="font-weight: 600; color: {risk_color};">{device['days_until_due']} Tage</div>
                </div>
                <div>
                    <div style="font-size: 0.75rem; color: #6b7280; margin-bottom: 0.25rem;">Betriebsstunden</div>
                    <div style="font-weight: 600; color: #1f2937;">{device['usage_hours']:,}</div>
                </div>
                <div>
                    <div style="font-size: 0.75rem; color: #6b7280; margin-bottom: 0.25rem;">Empfohlenes Wartungsfenster</div>
                    <div style="font-weight: 600; color: #667eea; font-size: 0.875rem;">{recommended_window_de}</div>
                </div>
                <div>
                    {risk_badge}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Geräterisikoverteilung
    st.markdown("---")
    st.markdown("#### Verteilung der Geräterisiken")
    st.markdown("")  # Abstand
    
    # German labels and color mapping
    risk_map = {'hoch': 'hoch', 'mittel': 'mittel', 'niedrig': 'niedrig', 'high': 'hoch', 'medium': 'mittel', 'low': 'niedrig'}
    label_map = {'hoch': 'Hoch', 'mittel': 'Mittel', 'niedrig': 'Niedrig'}
    color_map = {'hoch': '#DC2626', 'mittel': '#F59E0B', 'niedrig': '#10B981'}
    device_risk_counts = {'hoch': 0, 'mittel': 0, 'niedrig': 0}
    for device in devices:
        risk_level = risk_map.get(device['risk_level'], device['risk_level'])
        device_risk_counts[risk_level] = device_risk_counts.get(risk_level, 0) + 1

    x_labels = [label_map[k] for k in device_risk_counts.keys()]
    colors = [label_map[k] for k in device_risk_counts.keys()]
    color_discrete_map = {label_map[k]: color_map[k] for k in device_risk_counts.keys()}

    fig_device_risk = px.bar(
        x=x_labels,
        y=list(device_risk_counts.values()),
        title="",
        labels={'x': 'Risikostufe', 'y': 'Anzahl'},
        color=colors,
        color_discrete_map=color_discrete_map
    )
    fig_device_risk.update_layout(
        height=300,
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        xaxis_title="Risikostufe",
        yaxis_title="Anzahl Geräte"
    )
    st.plotly_chart(fig_device_risk, use_container_width=True)

# Sidebar footer
st.sidebar.markdown("---")
st.sidebar.markdown("")  # Spacing

if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
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
footer_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
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

