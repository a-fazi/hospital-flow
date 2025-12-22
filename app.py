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
    header {visibility: hidden;}
    
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

# Demo Mode toggle (in sidebar - must be early to avoid bug)
st.sidebar.markdown("---")
demo_mode = st.sidebar.toggle("🎬 Demo Mode", value=False, help="Increase event frequency for demonstration")
if demo_mode:
    st.sidebar.info("Demo mode: Events occur more frequently")
st.sidebar.markdown("---")

# Sticky Header with professional design
current_time = datetime.now().strftime('%H:%M:%S')
st.markdown(f"""
<div class="sticky-header">
    <div class="header-content">
        <div class="header-title">
            <span style="font-size: 1.75rem;">🏥</span>
            <span>HospitalFlow</span>
            <span style="font-size: 0.875rem; font-weight: 400; color: #6b7280; margin-left: 0.5rem;">Operations Dashboard</span>
        </div>
        <div style="display: flex; align-items: center; gap: 1rem;">
            <div class="status-badge" style="background: {status_color}15; color: {status_color}; border: 1px solid {status_color}30;">
                <span class="status-dot" style="background: {status_color};"></span>
                <span>{system_status.upper()}</span>
            </div>
            <div class="timestamp" style="font-size: 0.75rem; color: #6b7280;">{current_time}</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar navigation with professional styling
st.sidebar.markdown("""
<div style="padding: 0.5rem 0 1.5rem 0; border-bottom: 1px solid #e5e7eb; margin-bottom: 1rem;">
    <h3 style="color: #667eea; margin: 0; font-size: 1.125rem; font-weight: 600; letter-spacing: -0.01em;">Navigation</h3>
</div>
""", unsafe_allow_html=True)

# Severity Legend (compact and professional)
st.sidebar.markdown("""
<div class="legend" style="margin-bottom: 1rem;">
    <div style="font-size: 0.7rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem; font-weight: 600;">Severity</div>
    <div class="legend-item">
        <span class="badge" style="background: #DC2626; color: white; width: 10px; height: 10px; padding: 0; border-radius: 50%; display: inline-block;"></span>
        <span style="font-size: 0.75rem;">High</span>
    </div>
    <div class="legend-item">
        <span class="badge" style="background: #F59E0B; color: white; width: 10px; height: 10px; padding: 0; border-radius: 50%; display: inline-block;"></span>
        <span style="font-size: 0.75rem;">Medium</span>
    </div>
    <div class="legend-item">
        <span class="badge" style="background: #10B981; color: white; width: 10px; height: 10px; padding: 0; border-radius: 50%; display: inline-block;"></span>
        <span style="font-size: 0.75rem;">Low</span>
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
    <p class="page-subtitle">Last updated: {page_timestamp}</p>
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
        st.warning(f"⚠️ **Active Surge Event**: {remaining:.0f} minutes remaining (Intensity: {surge['intensity']:.1f})")
        st.markdown("")  # Spacing
    
    # Live Status Section
    st.markdown("### Live Status")
    st.markdown("")  # Spacing
    
    # 8 Metric Cards in 4x2 grid
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        severity_color = get_severity_color(ed_severity)
        badge_html = render_badge(ed_hint, ed_severity)
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: {severity_color};">
            <div style="font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600; margin-bottom: 0.75rem;">ED Load</div>
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
            <div style="font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600; margin-bottom: 0.75rem;">Waiting Count</div>
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
            <div style="font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600; margin-bottom: 0.75rem;">Beds Free</div>
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
            <div style="font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600; margin-bottom: 0.75rem;">Staff Load</div>
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
            <div style="font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600; margin-bottom: 0.75rem;">Rooms Free</div>
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
            <div style="font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600; margin-bottom: 0.75rem;">OR Load</div>
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
            <div style="font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600; margin-bottom: 0.75rem;">Transport Queue</div>
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
            <div style="font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600; margin-bottom: 0.75rem;">Inventory/Device Risk</div>
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
        st.markdown("### Trends (Last 60 Minutes)")
        st.markdown("")  # Spacing
        
        # Get historical data from simulation
        waiting_history = sim.get_metric_history('waiting_count', 60)
        ed_history = sim.get_metric_history('ed_load', 60)
        
        # Convert to DataFrames
        df_waiting = pd.DataFrame(waiting_history)
        df_waiting['timestamp'] = pd.to_datetime(df_waiting['timestamp'])
        
        df_ed = pd.DataFrame(ed_history)
        df_ed['timestamp'] = pd.to_datetime(df_ed['timestamp'])
        
        # Waiting count chart
        fig_waiting = px.line(
            df_waiting,
            x='timestamp',
            y='value',
            title="Waiting Count",
            labels={'value': 'Count', 'timestamp': ''}
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
        
        # ED Load chart
        fig_ed = px.line(
            df_ed,
            x='timestamp',
            y='value',
            title="ED Load",
            labels={'value': 'Load %', 'timestamp': ''}
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
        st.markdown("### Next 15 Min Outlook")
        st.markdown("")  # Spacing
        
        # Get top 3 predicted bottlenecks
        bottleneck_predictions = []
        for pred in predictions:
            if pred['time_horizon_minutes'] <= 15:
                bottleneck_predictions.append(pred)
        
        # Sort by predicted value (descending) and take top 3
        bottleneck_predictions.sort(key=lambda x: x['predicted_value'], reverse=True)
        top_bottlenecks = bottleneck_predictions[:3]
        
        if top_bottlenecks:
            for i, bottleneck in enumerate(top_bottlenecks, 1):
                pred_type = bottleneck['prediction_type'].replace('_', ' ').title()
                pred_value = bottleneck['predicted_value']
                pred_minutes = bottleneck['time_horizon_minutes']
                dept = bottleneck.get('department', 'N/A')
                
                st.markdown(f"""
                <div style="background: white; padding: 1rem; border-radius: 8px; margin-bottom: 0.75rem; border-left: 3px solid #667eea; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                    <div style="font-size: 0.875rem; font-weight: 600; color: #1f2937; margin-bottom: 0.25rem;">
                        {i}. {pred_type}
                    </div>
                    <div style="font-size: 1.25rem; font-weight: 700; color: #667eea; margin: 0.25rem 0;">
                        {pred_value:.0f}
                    </div>
                    <div style="font-size: 0.75rem; color: #6b7280; margin-top: 0.5rem;">
                        {dept} • In {pred_minutes} min
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(render_empty_state("📊", "No predicted bottlenecks", "System operating within normal parameters"), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Recent alerts
    st.markdown("### Recent Alerts")
    st.markdown("")  # Spacing
    if alerts:
        for alert in alerts[:5]:
            severity_color = get_severity_color(alert['severity'])
            badge_html = render_badge(alert['severity'].upper(), alert['severity'])
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
        st.info("No active alerts")
    
    # Pending recommendations
    st.markdown("### Pending Recommendations")
    st.markdown("")  # Spacing
    if recommendations:
        for rec in recommendations[:3]:
            priority_color = get_priority_color(rec['priority'])
            badge_html = render_badge(rec['priority'].upper(), rec['priority'])
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
        st.markdown(render_empty_state("✅", "No pending recommendations", "All recommendations have been reviewed"), unsafe_allow_html=True)

elif page == "Operations":
    # Operations page with tabs
    tab1, tab2, tab3 = st.tabs(["🚨 Alerts", "💡 Recommendations", "📝 Audit"])
    
    # Alerts Tab
    with tab1:
        st.markdown("### Alerts")
        st.markdown("")  # Spacing
        
        # Filter row
        col1, col2, col3 = st.columns([2, 2, 2])
        
        with col1:
            # Area dropdown
            all_alerts = db.get_alerts_by_time_range(24)
            areas = ["All"] + sorted(list(set([a.get('department', 'N/A') for a in all_alerts if a.get('department')])))
            selected_area = st.selectbox("Area", areas, key="ops_alert_area")
        
        with col2:
            # Severity chips
            severity_options = ["All", "high", "medium", "low"]
            selected_severities = st.multiselect(
                "Severity",
                severity_options,
                default=["high", "medium"],
                key="ops_alert_severity"
            )
            if not selected_severities:
                selected_severities = severity_options
        
        with col3:
            # Time range
            time_range = st.selectbox(
                "Time Range",
                ["Last 1 hour", "Last 6 hours", "Last 24 hours"],
                index=2,
                key="ops_alert_time"
            )
            hours_map = {"Last 1 hour": 1, "Last 6 hours": 6, "Last 24 hours": 24}
            hours = hours_map[time_range]
        
        st.markdown("")  # Spacing
        
        # Get filtered alerts
        alerts = db.get_alerts_by_time_range(hours)
        
        # Apply filters
        filtered_alerts = alerts
        if selected_area != "All":
            filtered_alerts = [a for a in filtered_alerts if a.get('department') == selected_area]
        if "All" not in selected_severities:
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
                
                col1, col2 = st.columns([5, 1])
                with col1:
                    pred_text = f" • Predicted: {predicted_minutes} min" if predicted_minutes else ""
                    st.markdown(f"""
                    <div style="background: white; padding: 1rem; border-radius: 8px; margin-bottom: 0.75rem; border-left: 4px solid {severity_color}; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                        <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem;">
                            {badge_html}
                            <span style="font-size: 0.75rem; color: #6b7280; font-weight: 500;">{alert.get('department', 'N/A')}</span>
                            <span style="font-size: 0.75rem; color: #9ca3af;">•</span>
                            <span style="font-size: 0.75rem; color: #6b7280;">{format_time_ago(alert['timestamp'])}</span>
                            {f'<span style="font-size: 0.75rem; color: #667eea;">{pred_text}</span>' if predicted_minutes else ''}
                        </div>
                        <div style="font-weight: 600; color: #1f2937; font-size: 0.95rem;">
                            {alert['message']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    if st.button("Acknowledge", key=f"ops_ack_{alert['id']}", use_container_width=True):
                        db.acknowledge_alert(alert['id'])
                        st.success("✅ Alert acknowledged")
                        st.rerun()
        else:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">🔍</div>
                <div class="empty-state-title">No alerts found</div>
                <div class="empty-state-text">No alerts match the selected filters</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Recommendations Tab
    with tab2:
        st.markdown("### Recommendations")
        st.markdown("")  # Spacing
        
        # Role selector pinned at top
        selected_role = st.radio(
            "Role",
            ["All", "Nurse", "Doctor", "Manager"],
            horizontal=True,
            key="ops_rec_role"
        )
        
        st.markdown("")  # Spacing
        
        # Get recommendations
        recommendations = db.get_pending_recommendations()
        
        # Filter by role (in real app, this would filter by actual role field)
        if selected_role != "All":
            # For MVP, we'll show all but could filter by rec_type or department
            pass
        
        if recommendations:
            for rec in recommendations:
                priority_color = get_priority_color(rec['priority'])
                badge_html = render_badge(rec['priority'].upper(), rec['priority'])
                
                # Get explanation score
                explanation_score = rec.get('explanation_score', 'medium')
                score_color = get_explanation_score_color(explanation_score)
                score_badge = render_badge(f"Confidence: {explanation_score.upper()}", explanation_score if explanation_score != 'low' else 'medium')
                
                # Impact tags (extract from department and rec_type)
                impact_tags = []
                if rec.get('department'):
                    impact_tags.append(rec['department'])
                if rec.get('rec_type'):
                    impact_tags.append(rec['rec_type'].replace('_', ' ').title())
                
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
                                <strong style="color: #1f2937; font-size: 0.875rem;">Action:</strong>
                                <p style="margin: 0.25rem 0 0 0; color: #4b5563; line-height: 1.6;">{rec.get('action', 'N/A')}</p>
                            </div>
                            <div style="margin-bottom: 0.75rem;">
                                <strong style="color: #1f2937; font-size: 0.875rem;">Reason:</strong>
                                <p style="margin: 0.25rem 0 0 0; color: #4b5563; line-height: 1.6;">{rec.get('reason', 'N/A')}</p>
                            </div>
                            <div style="margin-bottom: 0.75rem;">
                                <strong style="color: #1f2937; font-size: 0.875rem;">Expected impact:</strong>
                                <p style="margin: 0.25rem 0 0 0; color: #4b5563; line-height: 1.6;">{rec.get('expected_impact', 'N/A')}</p>
                            </div>
                            <div>
                                <strong style="color: #1f2937; font-size: 0.875rem;">Safety note:</strong>
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
                with st.expander("Why suggested?", expanded=False):
                    if has_new_format:
                        # Use the reason and expected_impact from the template
                        explanation = f"""
                        <strong>Reason:</strong> {rec.get('reason', 'N/A')}<br><br>
                        <strong>Expected Impact:</strong> {rec.get('expected_impact', 'N/A')}<br><br>
                        <strong>Confidence Level:</strong> {explanation_score.upper()} (based on trend strength and data quality)
                        """
                    else:
                        # Generate explanation based on rec_type
                        rec_type = rec.get('rec_type', 'general')
                        explanations = {
                            'capacity': f"Current capacity utilization in {rec.get('department', 'this area')} is above threshold. Historical data suggests opening overflow beds reduces wait times by 15-20%.",
                            'staffing': f"Staff load analysis shows {rec.get('department', 'this area')} is experiencing increased demand. Reallocation can improve response times.",
                            'inventory': f"Inventory levels for critical supplies in {rec.get('department', 'this area')} are below optimal. Reorder now to prevent stockout.",
                            'general': f"AI analysis of current metrics and trends in {rec.get('department', 'this area')} suggests this action to optimize operations."
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
                        "Action / Reason",
                        key=f"ops_action_{rec['id']}",
                        placeholder="Enter action taken or rejection reason"
                    )
                with col2:
                    col_accept, col_reject = st.columns(2)
                    with col_accept:
                        accept_clicked = st.button("✅ Accept", key=f"ops_accept_{rec['id']}", use_container_width=True, type="primary")
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
                                st.success("✅ Recommendation accepted")
                                st.rerun()
                            else:
                                st.warning("⚠️ Please enter action taken")
                    with col_reject:
                        reject_clicked = st.button("❌ Reject", key=f"ops_reject_{rec['id']}", use_container_width=True)
                        if reject_clicked:
                            if action_text:
                                db.reject_recommendation(rec['id'], action_text)
                                st.info("❌ Recommendation rejected")
                                st.rerun()
                            else:
                                st.warning("⚠️ Please enter rejection reason")
                
                st.markdown("---")
        else:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">✅</div>
                <div class="empty-state-title">No pending recommendations</div>
                <div class="empty-state-text">All recommendations have been reviewed</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Audit Tab
    with tab3:
        st.markdown("### Audit Log")
        st.markdown("")  # Spacing
        
        # Filters
        audit_log = db.get_audit_log(100)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            roles = ["All"] + sorted(list(set([a.get('user_role', 'system') for a in audit_log if a.get('user_role')])))
            selected_role_audit = st.selectbox("Role", roles, key="ops_audit_role")
        
        with col2:
            actions = ["All"] + sorted(list(set([a.get('action_type', '') for a in audit_log if a.get('action_type')])))
            selected_action = st.selectbox("Action", actions, key="ops_audit_action")
        
        with col3:
            areas = ["All"] + sorted(list(set([a.get('entity_type', '') for a in audit_log if a.get('entity_type')])))
            selected_area_audit = st.selectbox("Area", areas, key="ops_audit_area")
        
        st.markdown("")  # Spacing
        
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
            # Prepare data for table
            table_data = []
            for entry in filtered_audit:
                table_data.append({
                    "Time": format_time_ago(entry['timestamp']),
                    "Role": entry.get('user_role', 'system').title(),
                    "Action": entry['action_type'].replace('_', ' ').title(),
                    "Area": entry.get('entity_type', 'N/A'),
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
            st.info("No audit log entries found")

elif page == "Live Metrics":
    st.markdown("### Real-time Metrics")
    
    metrics = db.get_recent_metrics(20)
    if metrics:
        df = pd.DataFrame(metrics)
        
        # Group by metric type
        metric_types = df['metric_type'].unique()
        
        cols = st.columns(3)
        for idx, metric_type in enumerate(metric_types[:6]):
            col_idx = idx % 3
            with cols[col_idx]:
                latest = df[df['metric_type'] == metric_type].iloc[0]
                st.metric(
                    metric_type.replace('_', ' ').title(),
                    f"{latest['value']:.1f} {latest.get('unit', '')}",
                    delta=None
                )
        
        # Time series chart
        st.markdown("---")
        st.markdown("### Metric Trends")
        
        selected_metric = st.selectbox("Select metric type", metric_types, key="metric_select")
        metric_data = df[df['metric_type'] == selected_metric].sort_values('timestamp')
        
        if not metric_data.empty:
            fig = px.line(
                metric_data,
                x='timestamp',
                y='value',
                color='department',
                title=f"{selected_metric.replace('_', ' ').title()} Over Time",
                markers=True
            )
            fig.update_layout(
                height=400,
                xaxis_title="Time",
                yaxis_title="Value",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No metrics available")

elif page == "Predictions":
    st.markdown("### 5-15 Minute Predictions")
    
    predictions = db.get_predictions(15)
    if predictions:
        df = pd.DataFrame(predictions)
        
        # Group predictions
        st.markdown("#### Upcoming Predictions")
        for pred in predictions[:10]:
            confidence_color = "#10B981" if pred['confidence'] > 0.8 else "#F59E0B" if pred['confidence'] > 0.7 else "#EF4444"
            st.markdown(f"""
            <div style="background: white; padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>{pred['prediction_type'].replace('_', ' ').title()}</strong>
                        <div style="color: #6b7280; font-size: 0.875rem; margin-top: 0.25rem;">
                            {pred.get('department', 'N/A')} • {pred['time_horizon_minutes']} min ahead
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 1.5rem; font-weight: 700; color: #1f2937;">
                            {pred['predicted_value']:.1f}
                        </div>
                        <div style="font-size: 0.75rem; color: {confidence_color};">
                            {pred['confidence']*100:.0f}% confidence
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Prediction chart
        st.markdown("---")
        st.markdown("### Prediction Confidence by Time Horizon")
        
        if len(df) > 0:
            fig = px.scatter(
                df,
                x='time_horizon_minutes',
                y='confidence',
                size='predicted_value',
                color='prediction_type',
                hover_data=['department'],
                title=""
            )
            fig.update_layout(
                height=400,
                xaxis_title="Time Horizon (minutes)",
                yaxis_title="Confidence",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown(render_empty_state("🔮", "No predictions available", "Predictions will appear here when available"), unsafe_allow_html=True)

elif page == "Alerts":
    alerts = db.get_active_alerts()
    
    if alerts:
        # Filter options
        st.markdown("### Filters")
        col1, col2 = st.columns(2)
        with col1:
            severity_filter = st.selectbox("Filter by severity", ["All", "high", "medium", "low"], key="alert_severity")
        with col2:
            dept_filter = st.selectbox("Filter by department", ["All"] + list(set([a.get('department', 'N/A') for a in alerts])), key="alert_dept")
        
        filtered_alerts = alerts
        if severity_filter != "All":
            filtered_alerts = [a for a in filtered_alerts if a['severity'] == severity_filter]
        if dept_filter != "All":
            filtered_alerts = [a for a in filtered_alerts if a.get('department') == dept_filter]
        
        st.markdown("")  # Spacing
        st.markdown("### Active Alerts")
        st.markdown("")  # Spacing
        
        for alert in filtered_alerts:
            severity_color = get_severity_color(alert['severity'])
            badge_html = render_badge(alert['severity'].upper(), alert['severity'])
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.markdown(f"""
                <div style="background: white; padding: 1.25rem; border-radius: 8px; margin-bottom: 0.75rem; border-left: 4px solid {severity_color}; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                    {badge_html}
                    <strong style="margin-left: 0.5rem; color: #1f2937;">{alert['message']}</strong>
                    <div style="color: #6b7280; font-size: 0.875rem; margin-top: 0.75rem;">
                        {alert.get('department', 'N/A')} • {alert['alert_type']} • {format_time_ago(alert['timestamp'])}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if st.button("Acknowledge", key=f"ack_{alert['id']}", use_container_width=True):
                    db.acknowledge_alert(alert['id'])
                    st.rerun()
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">✅</div>
            <div class="empty-state-title">No critical alerts right now</div>
            <div class="empty-state-text">All systems operating normally</div>
        </div>
        """, unsafe_allow_html=True)

elif page == "Recommendations":
    st.markdown("### Pending Recommendations")
    st.markdown("Review and accept or reject AI-generated recommendations")
    st.markdown("")  # Spacing
    
    recommendations = db.get_pending_recommendations()
    
    if recommendations:
        for rec in recommendations:
            priority_color = get_priority_color(rec['priority'])
            badge_html = render_badge(rec['priority'].upper(), rec['priority'])
            
            # Get explanation score
            explanation_score = rec.get('explanation_score', 'medium')
            score_color = get_explanation_score_color(explanation_score)
            score_badge = render_badge(f"Confidence: {explanation_score.upper()}", explanation_score if explanation_score != 'low' else 'medium')
            
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
                            <strong style="color: #1f2937; font-size: 0.875rem;">Action:</strong>
                            <p style="margin: 0.25rem 0 0 0; color: #4b5563; line-height: 1.6;">{rec.get('action', 'N/A')}</p>
                        </div>
                        <div style="margin-bottom: 0.75rem;">
                            <strong style="color: #1f2937; font-size: 0.875rem;">Reason:</strong>
                            <p style="margin: 0.25rem 0 0 0; color: #4b5563; line-height: 1.6;">{rec.get('reason', 'N/A')}</p>
                        </div>
                        <div style="margin-bottom: 0.75rem;">
                            <strong style="color: #1f2937; font-size: 0.875rem;">Expected impact:</strong>
                            <p style="margin: 0.25rem 0 0 0; color: #4b5563; line-height: 1.6;">{rec.get('expected_impact', 'N/A')}</p>
                        </div>
                        <div>
                            <strong style="color: #1f2937; font-size: 0.875rem;">Safety note:</strong>
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
                action = st.text_input("Action taken / Reason", key=f"action_{rec['id']}", placeholder="Enter action or rejection reason")
            with col2:
                col_accept, col_reject = st.columns(2)
                with col_accept:
                    if st.button("✅ Accept", key=f"accept_{rec['id']}", use_container_width=True, type="primary"):
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
                            st.success("✅ Recommendation accepted")
                            st.rerun()
                        else:
                            st.warning("⚠️ Please enter action taken")
                with col_reject:
                    if st.button("❌ Reject", key=f"reject_{rec['id']}", use_container_width=True):
                        if action:
                            db.reject_recommendation(rec['id'], action)
                            st.info("❌ Recommendation rejected")
                            st.rerun()
                        else:
                            st.warning("⚠️ Please enter rejection reason")
            
            st.markdown("---")
    else:
        st.markdown(render_empty_state("✅", "No pending recommendations", "All recommendations have been reviewed"), unsafe_allow_html=True)

elif page == "Transport":
    st.markdown("### Transport Requests")
    
    transport = db.get_transport_requests()
    
    if transport:
        status_filter = st.selectbox("Filter by status", ["All", "pending", "in_progress", "completed"], key="transport_status")
        
        filtered_transport = transport
        if status_filter != "All":
            filtered_transport = [t for t in transport if t['status'] == status_filter]
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Pending", len([t for t in transport if t['status'] == 'pending']))
        with col2:
            st.metric("In Progress", len([t for t in transport if t['status'] == 'in_progress']))
        with col3:
            st.metric("Completed", len([t for t in transport if t['status'] == 'completed']))
        with col4:
            avg_time = sum([t['estimated_time_minutes'] or 0 for t in transport]) / len(transport) if transport else 0
            st.metric("Avg Est. Time", format_duration_minutes(int(avg_time)))
        
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
                            {f"• Est: {format_duration_minutes(trans['estimated_time_minutes'])}" if trans['estimated_time_minutes'] else ""}
                            {f"• Actual: {format_duration_minutes(trans['actual_time_minutes'])}" if trans['actual_time_minutes'] else ""}
                            • {format_time_ago(trans['timestamp'])}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(render_empty_state("🚑", "No transport requests", "No active transport requests at this time"), unsafe_allow_html=True)

elif page == "Inventory":
    st.markdown("### Inventory Status")
    
    inventory = db.get_inventory_status()
    
    if inventory:
        # Low stock alert
        low_stock = [i for i in inventory if i['current_stock'] < i['min_threshold']]
        if low_stock:
            st.warning(f"⚠️ {len(low_stock)} items below threshold")
        
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
                        Threshold: {item['min_threshold']} • Capacity: {item['max_capacity']}
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
        st.markdown("### Stock Levels")
        df_inv = pd.DataFrame(inventory)
        df_inv['utilization'] = (df_inv['current_stock'] / df_inv['max_capacity']) * 100
        
        fig = px.bar(
            df_inv,
            x='item_name',
            y='utilization',
            color='department',
            title="Inventory Utilization by Item",
            labels={'utilization': 'Utilization %', 'item_name': 'Item'}
        )
        fig.update_layout(
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No inventory data")

elif page == "Device Maintenance":
    st.markdown("### Device Maintenance Risk Assessment")
    
    devices = db.get_device_maintenance_risks()
    
    if devices:
        # Risk summary
        high_risk = len([d for d in devices if d['risk_level'] == 'high'])
        medium_risk = len([d for d in devices if d['risk_level'] == 'medium'])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("High Risk Devices", high_risk, delta=None)
        with col2:
            st.metric("Medium Risk Devices", medium_risk, delta=None)
        with col3:
            st.metric("Total Devices", len(devices))
        
        st.markdown("---")
        
        # Device cards
        for device in devices:
            risk_color = get_risk_color(device['risk_level'])
            status_color = get_status_color(device['status'])
            
            st.markdown(f"""
            <div style="background: white; padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid {risk_color};">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div style="flex: 1;">
                        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                            <span class="badge" style="background: {risk_color}; color: white;">{device['risk_level'].upper()} RISK</span>
                            <span class="badge" style="background: {status_color}; color: white;">{device['status'].upper()}</span>
                        </div>
                        <h4 style="margin: 0 0 0.5rem 0;">{device['device_type']} - {device['device_id']}</h4>
                        <div style="color: #6b7280; font-size: 0.875rem;">
                            <div>Department: {device.get('department', 'N/A')}</div>
                            <div>Usage: {device['usage_hours']} hours</div>
                            <div>Last Maintenance: {device['last_maintenance']}</div>
                            <div>Next Due: {device['next_maintenance_due']}</div>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Risk distribution chart
        st.markdown("---")
        st.markdown("### Risk Distribution")
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
        st.markdown(render_empty_state("🔧", "No device data", "Device maintenance data will appear here when available"), unsafe_allow_html=True)

elif page == "Discharge Planning":
    st.markdown("### Discharge Planning Overview")
    st.markdown("Aggregated discharge planning metrics by department")
    
    discharge = db.get_discharge_planning()
    
    if discharge:
        df_disch = pd.DataFrame(discharge)
        
        # Summary metrics
        total_ready = df_disch['ready_for_discharge_count'].sum()
        total_pending = df_disch['pending_discharge_count'].sum()
        avg_los = df_disch['avg_length_of_stay_hours'].mean()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Ready for Discharge", total_ready)
        with col2:
            st.metric("Pending Discharge", total_pending)
        with col3:
            st.metric("Avg Length of Stay", f"{avg_los:.1f} hours")
        
        st.markdown("---")
        
        # Department cards
        cols = st.columns(3)
        for idx, dept_data in enumerate(discharge):
            col_idx = idx % 3
            with cols[col_idx]:
                dept_color = get_department_color(dept_data['department'])
                st.markdown(f"""
                <div style="background: white; padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem; border-top: 4px solid {dept_color};">
                    <h4 style="margin: 0 0 1rem 0; color: {dept_color};">{dept_data['department']}</h4>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                        <span style="color: #6b7280;">Ready:</span>
                        <strong>{dept_data['ready_for_discharge_count']}</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                        <span style="color: #6b7280;">Pending:</span>
                        <strong>{dept_data['pending_discharge_count']}</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                        <span style="color: #6b7280;">Avg LOS:</span>
                        <strong>{dept_data['avg_length_of_stay_hours']:.1f}h</strong>
                    </div>
                    <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #e5e7eb;">
                        <div style="font-size: 0.75rem; color: #9ca3af; margin-bottom: 0.25rem;">Capacity Utilization</div>
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
                y=['ready_for_discharge_count', 'pending_discharge_count'],
                title="Discharge Status by Department",
                barmode='group',
                color_discrete_map={'ready_for_discharge_count': '#10B981', 'pending_discharge_count': '#F59E0B'}
            )
            fig.update_layout(
                height=300,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.bar(
                df_disch,
                x='department',
                y='avg_length_of_stay_hours',
                title="Average Length of Stay",
                color='department',
                color_discrete_map={dept: get_department_color(dept) for dept in df_disch['department']}
            )
            fig.update_layout(
                height=300,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown(render_empty_state("🏥", "No discharge planning data", "Discharge planning data will appear here when available"), unsafe_allow_html=True)

elif page == "Discharge":
    # Simulate expected discharges data
    now = datetime.now()
    
    # Generate expected discharges for next 12 hours (hourly buckets)
    hourly_discharges = []
    for hour in range(12):
        hour_time = now + timedelta(hours=hour)
        # Simulate discharge counts (higher in morning/afternoon, lower at night)
        if 8 <= hour < 12:  # Morning peak
            count = random.randint(3, 8)
        elif 12 <= hour < 18:  # Afternoon peak
            count = random.randint(2, 6)
        elif 18 <= hour < 22:  # Evening
            count = random.randint(1, 4)
        else:  # Night
            count = random.randint(0, 2)
        
        hourly_discharges.append({
            'hour': hour_time,
            'hour_label': hour_time.strftime('%H:00'),
            'count': count
        })
    
    # Calculate expected discharges in next 4 hours
    next_4h_discharges = sum([d['count'] for d in hourly_discharges[:4]])
    
    # Big metric for next 4 hours
    st.markdown("### Expected Discharges")
    st.markdown("")  # Spacing
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
            <div style="color: white; font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem; opacity: 0.9;">
                Expected Discharges in Next 4 Hours
            </div>
            <div style="color: white; font-size: 4rem; font-weight: 700; line-height: 1;">
                {next_4h_discharges}
            </div>
            <div style="color: white; font-size: 1rem; margin-top: 0.5rem; opacity: 0.9;">
                Aggregated count
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        next_8h_discharges = sum([d['count'] for d in hourly_discharges[:8]])
        st.metric("Next 8 Hours", next_8h_discharges, delta=None)
    
    with col3:
        next_12h_discharges = sum([d['count'] for d in hourly_discharges])
        st.metric("Next 12 Hours", next_12h_discharges, delta=None)
    
    st.markdown("---")
    
    # Timeline chart for next 12 hours
    st.markdown("### Expected Discharges Timeline (Next 12 Hours)")
    st.markdown("")  # Spacing
    
    df_timeline = pd.DataFrame(hourly_discharges)
    
    fig_timeline = px.bar(
        df_timeline,
        x='hour_label',
        y='count',
        title="",
        labels={'hour_label': 'Time', 'count': 'Expected Discharges'},
        color='count',
        color_continuous_scale='Blues'
    )
    fig_timeline.update_layout(
        height=400,
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis_title="",
        yaxis_title="Expected Discharges",
        showlegend=False,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='#e5e7eb', showline=False)
    )
    fig_timeline.update_traces(marker_line_width=0)
    st.plotly_chart(fig_timeline, use_container_width=True)
    
    st.markdown("---")
    
    # Recommendations section
    st.markdown("### Recommendations")
    st.markdown("")  # Spacing
    
    # Simulate recommendations based on discharge patterns
    recommendations = []
    
    # Check for cases that need earlier discharge planning
    high_discharge_hours = [d for d in hourly_discharges[:6] if d['count'] >= 5]
    if high_discharge_hours:
        total_high = sum([d['count'] for d in high_discharge_hours])
        recommendations.append({
            "type": "early_planning",
            "message": f"Start discharge planning earlier for {total_high} cases (aggregate)",
            "details": f"High discharge volume expected in next 6 hours. Early planning can reduce delays by 20-30%.",
            "priority": "medium"
        })
    
    # Check for potential bottlenecks
    peak_hour = max(hourly_discharges[:8], key=lambda x: x['count'])
    if peak_hour['count'] >= 6:
        recommendations.append({
            "type": "resource_allocation",
            "message": f"Allocate additional resources for {peak_hour['hour_label']} (expected {peak_hour['count']} discharges)",
            "details": f"Peak discharge time identified. Consider additional staff or transport capacity.",
            "priority": "high"
        })
    
    # Check for low discharge periods (opportunity for catch-up)
    low_discharge_hours = [d for d in hourly_discharges if d['count'] <= 1]
    if len(low_discharge_hours) >= 3:
        recommendations.append({
            "type": "catch_up",
            "message": f"Use low-activity periods for catch-up (3+ hours with ≤1 discharge expected)",
            "details": "Multiple low-activity periods identified. Good opportunity to process pending discharges.",
            "priority": "low"
        })
    
    if recommendations:
        for rec in recommendations:
            priority_color = get_priority_color(rec['priority'])
            badge_html = render_badge(rec['priority'].upper(), rec['priority'])
            
            st.markdown(f"""
            <div style="background: white; padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid {priority_color}; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <div style="display: flex; align-items: start; gap: 0.75rem; margin-bottom: 0.75rem;">
                    {badge_html}
                    <div style="flex: 1;">
                        <h4 style="margin: 0 0 0.5rem 0; color: #1f2937;">{rec['message']}</h4>
                        <p style="color: #6b7280; margin: 0; line-height: 1.6;">{rec['details']}</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(render_empty_state("💡", "No recommendations at this time", "All systems operating within normal parameters"), unsafe_allow_html=True)
    
    # Additional aggregated statistics
    st.markdown("---")
    st.markdown("### Statistics")
    st.markdown("")  # Spacing
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        peak_hour = max(hourly_discharges, key=lambda x: x['count'])
        st.metric("Peak Hour", peak_hour['hour_label'], delta=f"{peak_hour['count']} discharges")
    
    with col2:
        avg_per_hour = sum([d['count'] for d in hourly_discharges]) / len(hourly_discharges)
        st.metric("Avg per Hour", f"{avg_per_hour:.1f}", delta=None)
    
    with col3:
        total_12h = sum([d['count'] for d in hourly_discharges])
        st.metric("Total (12h)", total_12h, delta=None)
    
    with col4:
        low_hours = len([d for d in hourly_discharges if d['count'] <= 1])
        st.metric("Low Activity Hours", low_hours, delta=None)

elif page == "Capacity Overview":
    st.markdown("### Hospital Capacity Overview")
    
    capacity = db.get_capacity_overview()
    
    if capacity:
        df_cap = pd.DataFrame(capacity)
        
        # Overall metrics
        total_beds = df_cap['total_beds'].sum()
        occupied_beds = df_cap['occupied_beds'].sum()
        available_beds = df_cap['available_beds'].sum()
        overall_util = occupied_beds / total_beds if total_beds > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Beds", total_beds)
        with col2:
            st.metric("Occupied", occupied_beds)
        with col3:
            st.metric("Available", available_beds)
        with col4:
            cap_status = calculate_capacity_status(overall_util)
            st.metric("Overall Utilization", f"{cap_status['percentage']}%")
        
        st.markdown("---")
        
        # Department capacity cards
        for cap in capacity:
            cap_status = calculate_capacity_status(cap['utilization_rate'])
            dept_color = get_department_color(cap['department'])
            
            st.markdown(f"""
            <div style="background: white; padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid {cap_status['color']};">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h4 style="margin: 0; color: {dept_color};">{cap['department']}</h4>
                    <span class="badge" style="background: {cap_status['color']}; color: white;">{cap_status['status'].upper()}</span>
                </div>
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 1rem;">
                    <div>
                        <div style="font-size: 0.75rem; color: #6b7280; text-transform: uppercase;">Total</div>
                        <div style="font-size: 1.5rem; font-weight: 700; color: #1f2937;">{cap['total_beds']}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.75rem; color: #6b7280; text-transform: uppercase;">Occupied</div>
                        <div style="font-size: 1.5rem; font-weight: 700; color: #DC2626;">{cap['occupied_beds']}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.75rem; color: #6b7280; text-transform: uppercase;">Available</div>
                        <div style="font-size: 1.5rem; font-weight: 700; color: #10B981;">{cap['available_beds']}</div>
                    </div>
                </div>
                <div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                        <span style="font-size: 0.875rem; color: #6b7280;">Utilization</span>
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
            fig = px.bar(
                df_cap,
                x='department',
                y='utilization_rate',
                title="Utilization Rate by Department",
                color='department',
                color_discrete_map={dept: get_department_color(dept) for dept in df_cap['department']},
                labels={'utilization_rate': 'Utilization Rate'}
            )
            fig.update_layout(
                height=400,
                yaxis=dict(tickformat='.0%'),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = go.Figure(data=[
                go.Bar(name='Occupied', x=df_cap['department'], y=df_cap['occupied_beds'], marker_color='#DC2626'),
                go.Bar(name='Available', x=df_cap['department'], y=df_cap['available_beds'], marker_color='#10B981')
            ])
            fig.update_layout(
                title="Bed Availability by Department",
                height=400,
                barmode='stack',
                xaxis_title="",
                yaxis_title="Beds",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown(render_empty_state("📋", "No capacity data", "Capacity data will appear here when available"), unsafe_allow_html=True)

elif page == "Audit Log":
    st.markdown("### Audit Log")
    st.markdown("Track all system actions and changes")
    
    audit_log = db.get_audit_log(100)
    
    if audit_log:
        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            action_filter = st.selectbox(
                "Filter by action",
                ["All"] + list(set([a['action_type'] for a in audit_log])),
                key="audit_action"
            )
        with col2:
            limit = st.slider("Number of entries", 10, 100, 50, key="audit_limit")
        
        filtered_log = audit_log[:limit]
        if action_filter != "All":
            filtered_log = [a for a in filtered_log if a['action_type'] == action_filter]
        
        # Audit log table
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
        st.markdown(render_empty_state("📝", "No audit log entries", "Audit log entries will appear here when available"), unsafe_allow_html=True)

elif page == "Assets":
    # Inventory Risk Section
    st.markdown("### Inventory Risk")
    st.markdown("")  # Spacing
    
    # Simulated inventory materials with risk
    inventory_materials = [
        {"name": "Surgical Gloves (Nitrile)", "current_stock": 45, "min_threshold": 100, "max_capacity": 500, "unit": "boxes", "department": "Surgery", "days_until_stockout": 3},
        {"name": "IV Catheters (18G)", "current_stock": 12, "min_threshold": 50, "max_capacity": 300, "unit": "units", "department": "ER", "days_until_stockout": 2},
        {"name": "Antibiotic Solution (Ceftriaxone)", "current_stock": 8, "min_threshold": 30, "max_capacity": 200, "unit": "vials", "department": "ICU", "days_until_stockout": 1},
        {"name": "Oxygen Masks (Adult)", "current_stock": 25, "min_threshold": 40, "max_capacity": 150, "unit": "units", "department": "General Ward", "days_until_stockout": 5},
        {"name": "Defibrillator Pads", "current_stock": 6, "min_threshold": 20, "max_capacity": 100, "unit": "pairs", "department": "Cardiology", "days_until_stockout": 1},
    ]
    
    # Calculate risk for each material
    for material in inventory_materials:
        stock_percent = (material['current_stock'] / material['max_capacity']) * 100
        threshold_percent = (material['min_threshold'] / material['max_capacity']) * 100
        
        if material['current_stock'] < material['min_threshold']:
            if material['days_until_stockout'] <= 2:
                risk_level = "high"
            else:
                risk_level = "medium"
        else:
            risk_level = "low"
        
        material['risk_level'] = risk_level
        material['stock_percent'] = stock_percent
        material['threshold_percent'] = threshold_percent
    
    # Sort by risk (high first)
    inventory_materials.sort(key=lambda x: {'high': 1, 'medium': 2, 'low': 3}[x['risk_level']])
    top_5_materials = inventory_materials[:5]
    
    # Display top 5 materials table
    if top_5_materials:
        table_data = []
        for mat in top_5_materials:
            risk_color = get_severity_color(mat['risk_level'])
            risk_badge = render_badge(mat['risk_level'].upper(), mat['risk_level'])
            table_data.append({
                "Material": mat['name'],
                "Current Stock": f"{mat['current_stock']} {mat['unit']}",
                "Threshold": f"{mat['min_threshold']} {mat['unit']}",
                "Days Until Stockout": mat['days_until_stockout'],
                "Risk": risk_badge,
                "Department": mat['department']
            })
        
        df_inv = pd.DataFrame(table_data)
        # Convert Risk column to HTML for display
        st.markdown("#### Top 5 Materials at Risk")
        st.markdown("")  # Spacing
        
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
                        <div style="font-size: 0.75rem; color: #6b7280; margin-bottom: 0.25rem;">Current</div>
                        <div style="font-weight: 600; color: #1f2937;">{mat['current_stock']} {mat['unit']}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.75rem; color: #6b7280; margin-bottom: 0.25rem;">Threshold</div>
                        <div style="font-weight: 600; color: #1f2937;">{mat['min_threshold']} {mat['unit']}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.75rem; color: #6b7280; margin-bottom: 0.25rem;">Days Left</div>
                        <div style="font-weight: 600; color: {risk_color};">{mat['days_until_stockout']} days</div>
                    </div>
                    <div>
                        {risk_badge}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Restock suggestions
    st.markdown("---")
    st.markdown("#### Restock Suggestions")
    st.markdown("")  # Spacing
    
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
                            Current: {suggestion['current']} → Suggested: {suggestion['suggested_qty']} units
                        </div>
                    </div>
                    <div style="font-weight: 600; color: {priority_color};">
                        +{suggestion['suggested_qty'] - suggestion['current']} units
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(render_empty_state("📦", "No restock suggestions", "All inventory levels are adequate"), unsafe_allow_html=True)
    
    # Risk distribution chart
    st.markdown("---")
    st.markdown("#### Risk Distribution")
    st.markdown("")  # Spacing
    
    risk_counts = {'high': 0, 'medium': 0, 'low': 0}
    for mat in inventory_materials:
        risk_counts[mat['risk_level']] = risk_counts.get(mat['risk_level'], 0) + 1
    
    fig_risk = px.bar(
        x=list(risk_counts.keys()),
        y=list(risk_counts.values()),
        title="",
        labels={'x': 'Risk Level', 'y': 'Count'},
        color=list(risk_counts.keys()),
        color_discrete_map={'high': '#DC2626', 'medium': '#F59E0B', 'low': '#10B981'}
    )
    fig_risk.update_layout(
        height=300,
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        xaxis_title="",
        yaxis_title="Number of Materials"
    )
    st.plotly_chart(fig_risk, use_container_width=True)
    
    st.markdown("---")
    
    # Devices Risk Section
    st.markdown("### Devices Risk")
    st.markdown("")  # Spacing
    
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
    st.markdown("#### Device Maintenance Status")
    st.markdown("")  # Spacing
    
    for device in devices:
        risk_color = get_severity_color(device['risk_level'])
        risk_badge = render_badge(device['risk_level'].upper(), device['risk_level'])
        st.markdown(f"""
        <div style="background: white; padding: 1rem; border-radius: 8px; margin-bottom: 0.75rem; border-left: 4px solid {risk_color}; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
            <div style="display: grid; grid-template-columns: 2fr 1fr 1fr 1fr 1fr 1fr; gap: 1rem; align-items: center;">
                <div>
                    <div style="font-weight: 600; color: #1f2937; margin-bottom: 0.25rem;">{device['name']}</div>
                    <div style="font-size: 0.75rem; color: #6b7280;">{device['device_id']} • {device['department']}</div>
                </div>
                <div>
                    <div style="font-size: 0.75rem; color: #6b7280; margin-bottom: 0.25rem;">Type</div>
                    <div style="font-weight: 600; color: #1f2937;">{device['type']}</div>
                </div>
                <div>
                    <div style="font-size: 0.75rem; color: #6b7280; margin-bottom: 0.25rem;">Days Until Due</div>
                    <div style="font-weight: 600; color: {risk_color};">{device['days_until_due']} days</div>
                </div>
                <div>
                    <div style="font-size: 0.75rem; color: #6b7280; margin-bottom: 0.25rem;">Usage Hours</div>
                    <div style="font-weight: 600; color: #1f2937;">{device['usage_hours']:,}</div>
                </div>
                <div>
                    <div style="font-size: 0.75rem; color: #6b7280; margin-bottom: 0.25rem;">Maintenance Window</div>
                    <div style="font-weight: 600; color: #667eea; font-size: 0.875rem;">{device['recommended_window']}</div>
                </div>
                <div>
                    {risk_badge}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Device risk distribution chart
    st.markdown("---")
    st.markdown("#### Device Risk Distribution")
    st.markdown("")  # Spacing
    
    device_risk_counts = {'high': 0, 'medium': 0, 'low': 0}
    for device in devices:
        device_risk_counts[device['risk_level']] = device_risk_counts.get(device['risk_level'], 0) + 1
    
    fig_device_risk = px.bar(
        x=list(device_risk_counts.keys()),
        y=list(device_risk_counts.values()),
        title="",
        labels={'x': 'Risk Level', 'y': 'Count'},
        color=list(device_risk_counts.keys()),
        color_discrete_map={'high': '#DC2626', 'medium': '#F59E0B', 'low': '#10B981'}
    )
    fig_device_risk.update_layout(
        height=300,
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        xaxis_title="",
        yaxis_title="Number of Devices"
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
    <p style="margin: 0.25rem 0;">Aggregated data only</p>
    <p style="margin: 0.25rem 0;">No personal information</p>
</div>
""", unsafe_allow_html=True)

# Professional Footer with Privacy & Ethics
footer_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
st.markdown(f"""
<div class="footer">
    <div class="footer-content">
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 2.5rem; margin-bottom: 2rem;">
            <div>
                <h4 style="color: #111827; font-size: 0.9375rem; font-weight: 700; margin-bottom: 1rem; letter-spacing: -0.01em;">Privacy</h4>
                <p style="color: #4b5563; font-size: 0.8125rem; line-height: 1.7; margin: 0;">
                    All data displayed is aggregated and anonymized. No personal health information (PHI) or patient identifiers are stored or displayed. Data is used solely for operational insights.
                </p>
            </div>
            <div>
                <h4 style="color: #111827; font-size: 0.9375rem; font-weight: 700; margin-bottom: 1rem; letter-spacing: -0.01em;">Ethics</h4>
                <p style="color: #4b5563; font-size: 0.8125rem; line-height: 1.7; margin: 0;">
                    AI recommendations are suggestions only. All decisions remain human-in-the-loop. Staff maintain full control over patient care decisions. System supports, never replaces, clinical judgment.
                </p>
            </div>
            <div>
                <h4 style="color: #111827; font-size: 0.9375rem; font-weight: 700; margin-bottom: 1rem; letter-spacing: -0.01em;">Data Usage</h4>
                <p style="color: #4b5563; font-size: 0.8125rem; line-height: 1.7; margin: 0;">
                    Metrics, predictions, and recommendations are based on operational data patterns. All actions are logged in the audit trail for transparency and accountability.
                </p>
            </div>
        </div>
        <div style="text-align: center; padding-top: 1.5rem; border-top: 1px solid #e5e7eb;">
            <p style="color: #9ca3af; font-size: 0.75rem; margin: 0; font-weight: 500;">
                HospitalFlow MVP v1.0 • Built for hospital operations • Last updated: {footer_timestamp}
            </p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

