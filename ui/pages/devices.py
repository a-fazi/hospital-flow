"""
Seitenmodul für Gerätewartung
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import random
from utils import (
    format_time_ago, get_severity_color, get_priority_color, get_risk_color,
    get_status_color, calculate_inventory_status, calculate_capacity_status,
    format_duration_minutes, get_department_color, get_system_status,
    get_metric_severity_for_load, get_metric_severity_for_count, get_metric_severity_for_free,
    get_explanation_score_color
)
from ui.components import render_badge, render_empty_state


def render(db, sim, get_cached_alerts=None, get_cached_recommendations=None, get_cached_capacity=None):
    """Rendert die Gerätewartung-Seite"""
    st.markdown("### Gerätewartungs-Risikoanalyse")
    
    devices = db.get_device_maintenance_risks()
    
    if devices:
        # Risikozusammenfassung
        high_risk = len([d for d in devices if d['risk_level'] in ['high', 'hoch']])
        medium_risk = len([d for d in devices if d['risk_level'] in ['medium', 'mittel']])

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
                'high': 'HOCH',
                'medium': 'MITTEL',
                'low': 'NIEDRIG',
                'hoch': 'HOCH',
                'mittel': 'MITTEL',
                'niedrig': 'NIEDRIG'
            }.get(device['risk_level'], device['risk_level'].upper())
            status_label = {
                'active': 'AKTIV',
                'inactive': 'INAKTIV',
                'maintenance': 'IN WARTUNG',
                'pending': 'AUSSTEHEND',
                'in_use': 'IN BENUTZUNG',
                'in_betrieb': 'IN BETRIEB',
                'available': 'VERFÜGBAR',
                'unavailable': 'NICHT VERFÜGBAR',
                'in_progress': 'IN BEARBEITUNG',
                'completed': 'ABGESCHLOSSEN'
            }.get(device['status'], device['status'].replace('_', ' ').upper())
            
            st.html(f"""
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
            """)
        
        # Risk distribution chart
        st.markdown("---")
        st.markdown("### Risikoverteilung")
        df_dev = pd.DataFrame(devices)
        risk_counts = df_dev['risk_level'].value_counts()
        
        # Map German risk levels to display names for pie chart
        risk_label_map = {'high': 'Hoch', 'medium': 'Mittel', 'low': 'Niedrig', 'hoch': 'Hoch', 'mittel': 'Mittel', 'niedrig': 'Niedrig'}
        risk_display_names = [risk_label_map.get(name, name) for name in risk_counts.index]
        
        fig = px.pie(
            values=risk_counts.values,
            names=risk_display_names,
            color=risk_counts.index,
            color_discrete_map={
                'high': '#DC2626',
                'medium': '#F59E0B',
                'low': '#10B981',
                'hoch': '#DC2626',
                'mittel': '#F59E0B',
                'niedrig': '#10B981'
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
